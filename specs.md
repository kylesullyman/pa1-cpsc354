Kyle Sullivan  
2454608  
Professor Jonathan Weinberger  
CPSC 354

# Calculator Specification

## Context-free grammar

The starting grammar (exp -> exp '+' exp | exp '-' exp | exp '\*' exp | exp '^' exp | '-' exp | 'log' exp 'base' exp | '(' exp ')' | number) is ambiguous: 1+2\*3 could be (1+2)\*3 or 1+(2\*3), and 2^3^2 could group either way.
```
exp  -> exp '+' exp1 | exp '-' exp1 | exp1               
exp1 -> exp1 '*' exp2 | exp2                             
exp2 -> '-' exp2 | exp3                                  
exp3 -> exp4 '^' exp2 | exp4                             
exp4 -> number | '(' exp ')' | 'log' exp 'base' exp4    
```

## Order of operations with some examples
From loosest to tightest binding: binary + and -, then *, then unary -, then ^, then atoms (numbers, brackets, log). A higher-numbered level binds tighter. Left recursion makes +, - and * left-associative, and right recursion makes ^ right-associative, so 2^3^2 = 2^9 = 512. Unary minus binds looser than ^, -3^2 = -(3^2) = -9. The right operand of ^ is exp2, so negative exponents parse (2^-1 = 0.5). Brackets and log’s argument are enclosed on both sides, so they can be any expression. log’s base is only an atom, so log 8 base 2 + 1 = (log 8 base 2) + 1 = 4

## How the program runs

1. Grammar loading: the program reads grammar.lark from the scripts directory
2. Parsing / parser: parser gets initialized at import time and then the parser turns the input argv string into a CST
4. AST construction: CalcTransformer().transform(cst) converts the CST into an AST
5. Evaluation: evaluate(ast) computes the value, and print(format_result(result)) prints it.

## Methods
CalcTransformer(Transformer): defines one method per alias in the grammar. Each method returns a tuple:
- plus(items) -> ("plus", left, right)
- minus(items) -> ("minus", left, right)
- times(items) -> ("times", left, right)
- pow(items) -> ("pow", base, exponent)
- neg(items) -> ("neg", operand)
- log(items) -> ("log", argument, base)
- num(items) -> ("num", float(token))

evaluate(ast): a recursive function that checks based on the tag ast[0]

format_result(value): fix floating points for result formatting