import lexer

class Binary_expr:
    def __init__(self,left, operator, right):
        self.left = left
        self.operator: lexer.token= operator
        self.right = right
    def eval(self):
        pass
        
class parser:
    def __init__(self, tokens):
        self.tokens: list[lexer.token] = tokens
        self.position: int = 0
        self.
    def parse(self):
        
        pass