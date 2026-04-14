import lexer

class Number:
    """整數常數節點。"""

    def __init__(self, value):
        self.value = value


class Char:
    """字元常數節點。"""

    def __init__(self, char: str):
        self.value: str = char


class String:
    """字串常數節點。"""

    def __init__(self, string: str):
        self.value: str = string


class Identifier:
    """識別字節點，通常代表變數或函式名稱。"""

    def __init__(self, name: str):
        self.name = name


class Pointer:
    """指標包裝節點。"""

    def __init__(self, dtype, value):
        self.dtype = dtype
        self.value = value


class BinaryExpr:
    """二元運算節點，例如 +、-、&&、||、==。"""

    def __init__(self, left, operator, right):
        self.left = left
        self.operator: lexer.token = operator
        self.right = right


class UnaryExpr:
    """一元運算節點，支援前綴與後綴形式。"""

    def __init__(self, operator: lexer.token, operand, postfix=False):
        self.operator = operator
        self.operand = operand
        self.postfix = postfix


class AssignmentExpr:
    """指定運算節點，包含 = 與複合指定運算子。"""

    def __init__(self, left, operator: lexer.token, right):
        self.left = left
        self.operator = operator
        self.right = right


class CallExpr:
    """函式呼叫節點。"""

    def __init__(self, callee, args):
        self.callee = callee
        self.args = args


class IndexExpr:
    """陣列索引節點。"""

    def __init__(self, base, index):
        self.base = base
        self.index = index


class TypeSpec:
    """型別描述節點，例如 int、char*、void。"""

    def __init__(self, base_type: str, pointer_level: int = 0):
        self.base_type = base_type
        self.pointer_level = pointer_level


class parser:

    def __init__(self, tokens):
        self.tokens: list[lexer.token] = tokens
        self.current_token: lexer.token = self.tokens[0] if self.tokens else None
        self.position: int = 0
    