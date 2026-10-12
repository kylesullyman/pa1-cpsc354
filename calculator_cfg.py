# Kyle Sullivan
# 2454608
# Professor Jonathan Weinberger
# CPSC 354

import math
import sys

from lark import Lark, Transformer

# Load the grammar from grammar.lark
with open("grammar.lark", "r") as grammar_file:
    grammar = grammar_file.read()

# Create a Lark parser from the grammar
parser = Lark(grammar, parser="lalr")


# Transform CST to AST
class CalcTransformer(Transformer):
    def plus(self, items):
        return ("plus", items[0], items[1])

    def minus(self, items):
        return ("minus", items[0], items[1])

    def times(self, items):
        return ("times", items[0], items[1])

    def pow(self, items):
        return ("pow", items[0], items[1])

    def neg(self, items):
        return ("neg", items[0])

    def log(self, items):
        return ("log", items[0], items[1])

    def num(self, items):
        return ("num", float(items[0]))


# Evaluate the AST
def evaluate(ast):
    if ast[0] == "plus":
        return evaluate(ast[1]) + evaluate(ast[2])
    elif ast[0] == "minus":
        return evaluate(ast[1]) - evaluate(ast[2])
    elif ast[0] == "times":
        return evaluate(ast[1]) * evaluate(ast[2])
    elif ast[0] == "pow":
        return evaluate(ast[1]) ** evaluate(ast[2])
    elif ast[0] == "neg":
        return -evaluate(ast[1])
    elif ast[0] == "log":
        return math.log(evaluate(ast[1]), evaluate(ast[2]))
    elif ast[0] == "num":
        return ast[1]
    else:
        raise ValueError(f"Unknown operation: {ast}")


def format_result(value):
    if isinstance(value, float) and math.isfinite(value):
        rounded = round(value)
        if math.isclose(value, rounded, rel_tol=1e-9, abs_tol=1e-9):
            return str(rounded)
    return str(value)


# Main execution
if __name__ == "__main__":
    calc_transformer = CalcTransformer()
    input_string = sys.argv[1]
    cst = parser.parse(input_string)
    # print(cst)
    ast = calc_transformer.transform(cst)
    # print(ast)
    result = evaluate(ast)
    print(format_result(result))
