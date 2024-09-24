from lark import Lark, Transformer
import sys

# Load the grammar from grammarl.lark
with open("grammar.lark", "r") as grammar_file:
    grammar = grammar_file.read()

# Create a Lark parser
parser = Lark(grammar, parser='lalr')

# Define an AST transformer
# In this special case the transformer is the identity function
class CalcTransformer(Transformer):
    def plus(self, items):
        return ('plus', items[0], items[1])
    
    def times(self, items):
        return ('times', items[0], items[1])
    
    def num(self, items):
        return float(items[0])

# Function to evaluate the AST
def evaluate(ast):
    if isinstance(ast, tuple):
        if ast[0] == 'plus':
            return evaluate(ast[1]) + evaluate(ast[2])
        elif ast[0] == 'times':
            return evaluate(ast[1]) * evaluate(ast[2])
    else:
        return ast

# Main execution
if __name__ == "__main__":
    calc_transformer = CalcTransformer() 
    input_string = sys.argv[1]
    tree = parser.parse(input_string)  # Add this line
    #print(tree)
    ast = calc_transformer.transform(tree)
    #print(ast)
    result = evaluate(ast)
    print(result)
