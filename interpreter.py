import parser
import memory
import symtable as symtable


class Interpreter:
    def __init__(self,symbol_table: symtable=None, memory: memory.VirtualMemory=None):
        self.memory = memory
        self.symtable = symbol_table
    def evaluate(self, ast_node):
        if isinstance(ast_node, parser.Number):
            return ast_node.value
        elif isinstance(ast_node, parser.String):
            return ast_node.value
        elif isinstance(ast_node, parser.Identifier):
            pass # 這裡要實作變數取值邏輯，從符號表查地址再從記憶體取值
        elif isinstance(ast_node, parser.Pointer):
            pass # 這裡要實作指標取值邏輯，類似 C 語言的 *ptr
        elif isinstance(ast_node, parser.BinaryExpr):
            left_val = self.evaluate(ast_node.left)
            right_val = self.evaluate(ast_node.right)
            if ast_node.operator == "+":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '+' to {type(left_val).__name__} and {type(right_val).__name__} at line {ast_node.line}.")
                return left_val + right_val
            elif ast_node.operator == "-":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '-' to {type(left_val).__name__} and {type(right_val).__name__} at line {ast_node.line}.")
                return left_val - right_val
            elif ast_node.operator == "*":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '*' to {type(left_val).__name__} and {type(right_val).__name__} at line {ast_node.line}.")
                return left_val * right_val
            elif ast_node.operator == "/":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '/' to {type(left_val).__name__} and {type(right_val).__name__} at line {ast_node.line}.")
                return left_val / right_val