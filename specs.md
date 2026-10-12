# Calculator Specification

## Overview

`calculator_cfg.py` is a command-line calculator. It takes one argument, an arithmetic expression, and prints its value:

```
python calculator_cfg.py "1+2*3"
7
```

The program runs in four stages:

1. **Grammar loading.** It reads `grammar.lark` from the script's own directory.
2. **Parsing.** Lark builds an LALR(1) parser from the grammar. The parser turns the input string into a concrete syntax tree (CST, a Lark `Tree`).
3. **AST construction.** `CalcTransformer` walks the CST bottom-up and turns it into an abstract syntax tree (AST) made of nested Python tuples.
4. **Evaluation.** `evaluate` walks the AST recursively and computes a number. `format_result` then prints that number.

## Supported Operations

| Syntax | Meaning | AST node |
|---|---|---|
| `a + b` | addition | `("plus", a, b)` |
| `a - b` | subtraction | `("minus", a, b)` |
| `a * b` | multiplication | `("times", a, b)` |
| `a ^ b` | exponentiation | `("pow", a, b)` |
| `- a` | unary negation | `("neg", a)` |
| `log a base b` | logarithm of `a` in base `b` | `("log", a, b)` |
| `( a )` | grouping | *(no node; the inner AST is passed through)* |
| `NUMBER` | numeric literal (Lark's `common.NUMBER`, integer or decimal) | `("num", float)` |

## The Grammar

### Starting grammar (ambiguous)

```
exp -> exp '+' exp
exp -> exp '*' exp
exp -> exp '^' exp
exp -> exp '-' exp
exp -> '-' exp
exp -> 'log' exp 'base' exp
exp -> '(' exp ')'
exp -> number
```

This grammar is ambiguous. For example, `1+2*3` has two parse trees, `(1+2)*3` and `1+(2*3)`. Likewise, `2^3^2` can be read as `(2^3)^2` or `2^(3^2)`. The grammar says nothing about precedence or associativity.

### Modified grammar (unambiguous)

`grammar.lark` accepts the same language but gives every input exactly one parse tree. It does this with a **precedence ladder**: one nonterminal per precedence level. Each level can only produce operands from its own level or a tighter one. The only way back up to a looser level is through brackets: `( … )` or `log … base`.

In traditional CFG notation:

```
exp  -> exp '+' exp1   | exp '-' exp1   | exp1      (level 0: + and -, left-assoc)
exp1 -> exp1 '*' exp2  | exp2                       (level 1: *, left-assoc)
exp2 -> '-' exp2       | exp3                       (level 2: unary -)
exp3 -> exp4 '^' exp2  | exp4                       (level 3: ^, right-assoc)
exp4 -> number | '(' exp ')' | 'log' exp 'base' exp4   (level 4: atoms)
```

Lark details:

- A `?` before a rule name (`?exp`, `?exp1`, …) inlines that rule when it has only one child. Pass-through steps such as `exp -> exp1 -> exp2 -> …` therefore do not show up in the tree.
- `-> plus`, `-> minus`, `-> times`, `-> neg`, `-> pow`, `-> log` and `-> num` are aliases. They name the tree node an alternative produces, and each name matches a method in `CalcTransformer`.
- Literal strings such as `"+"` and `"log"` are anonymous tokens and are filtered out of the tree. Only the operands remain as children.
- `%import common.NUMBER` brings in Lark's number token. `%import common.WS` together with `%ignore WS` makes whitespace insignificant, so `log 8 base 2` and `1 + 2` parse correctly.
- The grammar is LALR(1): Lark builds the parser with `parser="lalr"` and reports no conflicts.

## Order of Operations

From loosest binding (evaluated last) to tightest binding (evaluated first):

| Level | Operators | Associativity | How it is enforced |
|---|---|---|---|
| 0 | binary `+`, `-` | left | `exp -> exp '+' exp1`: the recursion is on the **left**, so `5-2-1` is `(5-2)-1 = 2` |
| 1 | `*` | left | `exp1 -> exp1 '*' exp2`: left recursion |
| 2 | unary `-` | prefix (nests) | `exp2 -> '-' exp2`: recursion on itself, so `--1 = -(-1) = 1` |
| 3 | `^` | right | `exp3 -> exp4 '^' exp2`: the recursion is on the **right**, so `2^3^2 = 2^(3^2) = 512` |
| 4 | numbers, `( )`, `log … base …` | — | atoms |

### Design decisions

- **`*` binds tighter than `+`/`-`.** `*` lives one level deeper (`exp1`), so `1+2*3` can only parse as `1+(2*3) = 7`.
- **`^` binds tighter than `*` and `+`.** So `2^3*2 = (2^3)*2 = 16` and `2^3+1 = (2^3)+1 = 9`.
- **`^` is right-associative.** This matches the usual mathematical convention, `2^3^2 = 2^9 = 512`. The right operand of `^` is `exp2` (which includes `exp3`), so the chain keeps growing to the right. The left operand is `exp4` (an atom), so it cannot.
- **Unary minus binds looser than `^`.** As in standard math notation, `-3^2 = -(3^2) = -9`, not `(-3)^2 = 9`. This works because `neg` (level 2) sits *above* `pow` (level 3): its operand `exp2` can be a whole power expression, while the base of a power (`exp4`) can never start with `-`.
- **Negative exponents are allowed.** The right operand of `^` is `exp2`, which includes unary minus, so `2^-1 = 0.5` parses. The level-2 rule also lets `2*-3 = -6` parse.
- **Unary minus binds tighter than `*`.** `-2*3` is `(-2)*3`. Numerically this always gives the same result as `-(2*3)`, so the choice does not affect output.
- **`log … base …`.** The first operand is enclosed between the keywords `log` and `base`, so it can be any full `exp` without causing ambiguity (`log 2^3 base 2 = 3`). The base is restricted to an atom (`exp4`), so the log expression ends right after the base. As a result, `log 8 base 2 + 1` parses as `(log 8 base 2) + 1 = 4` and `log 8 base 2 * 3 = 9`. To use a compound base, write it in brackets: `log 8 base (1+1)`.
- **Brackets reset precedence.** `"(" exp ")"` is at the tightest level but contains a loosest-level `exp`, so `2-(4+2) = -4` and `(3+2)*2 = 10`.

## Code Structure (`calculator_cfg.py`)

### Module-level setup

- `grammar_path` is built from `os.path.dirname(os.path.abspath(__file__))`, so `grammar.lark` is found even when the script runs from a different working directory.
- `parser = Lark(grammar, parser="lalr")` builds the LALR parser once, when the module is imported.

### `class CalcTransformer(Transformer)`

A Lark `Transformer` visits the CST **bottom-up**. For each tree node whose name is `X`, it calls the method `X(self, items)`. `items` holds the node's children, which have already been transformed. Each method returns a tuple AST node:

- `plus(items)` returns `("plus", left, right)`
- `minus(items)` returns `("minus", left, right)`
- `times(items)` returns `("times", left, right)`
- `pow(items)` returns `("pow", base, exponent)`
- `neg(items)` returns `("neg", operand)`. It has a single child because the `"-"` token is filtered out.
- `log(items)` returns `("log", argument, base)`. The `"log"`/`"base"` keywords are filtered out, leaving two children.
- `num(items)` returns `("num", float(token))`. It converts the `NUMBER` token's text into a Python float.

Brackets have no alias. Their node is inlined by `?exp4`, so the inner AST passes through unchanged. The finished AST contains only the node types listed above, with no grammar details such as `exp1` or `exp2`.

Example: `-3^2` gives the CST `neg(pow(num 3, num 2))`, which becomes the AST `("neg", ("pow", ("num", 3.0), ("num", 2.0)))`.

### `evaluate(ast)`

A recursive function. It dispatches on the tag `ast[0]`:

- `"num"`: base case, returns `ast[1]`.
- `"plus"` / `"minus"` / `"times"`: evaluates both children recursively and combines them with `+`, `-`, `*`.
- `"pow"`: `evaluate(base) ** evaluate(exponent)`.
- `"neg"`: `-evaluate(operand)`.
- `"log"`: `math.log(evaluate(argument), evaluate(base))`.
- Any other tag raises `ValueError`.

The parser has already fixed the shape of the tree, so `evaluate` needs no knowledge of precedence. It just evaluates children before parents (post-order).

### `format_result(value)`

All arithmetic is done in floats, so results like `7.0`, or `2.9999999999999996` from `log 1000 base 10`, are common. If the result is a finite float within `1e-9` of an integer, `format_result` prints it as that integer (`7`, `3`). Otherwise it prints the float as is (`0.5`).

### Main block

```
input_string = sys.argv[1]
cst    = parser.parse(input_string)        # string -> CST
ast    = CalcTransformer().transform(cst)  # CST -> AST
result = evaluate(ast)                     # AST -> number
print(format_result(result))
```

## Testing

`python testing.py` runs every case in `testing-data.txt`. That includes all the cases from the assignment (`1+2*3`, `2-(4+2)`, `(3+2)*2`, `--1`, `2^3^2`, `2^3+1`, `2^3*2`, `log 8 base 2`, `log 8 base 2 + 1`, `-3^2`) plus extra cases for left-associative subtraction, negative exponents, unary minus after `*`, compound log arguments, and decimal input.
