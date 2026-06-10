import importlib.util
import os
import inspect
import random
import parser
import memory
import symtable as symtable
from extra_c_type import char_ptr, int_ptr,array
"""C-like 直譯器核心。

這個模組負責把 parser 產生的 AST 逐步求值，並透過虛擬記憶體與符號表
模擬 C 語言的變數、指標與函式呼叫行為。
"""

# 將 Python 執行時的型別名稱轉成錯誤訊息中較接近 C 語言的型別名稱。
type_mapping = {
    'int': 'int',
    'char_ptr': 'char*',
    'int_ptr': 'int*',
    'array': 'array',
    'None': 'void',
}

def c_div(left: int, right: int) -> int:
    """C-style integer division: truncate toward zero, unlike Python // for negatives."""
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


def c_mod(left: int, right: int) -> int:
    """C-style remainder: same sign as dividend and consistent with c_div()."""
    return left - c_div(left, right) * right

# 用 importlib 按路徑載入本地 builtins.py，
# 避免與 Python 內建的 builtins 模組（存放 print/len 等）同名衝突。
# 直接 `import builtins` 只會得到 Python 自己的模組，永遠拿不到本地檔案。
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "builtins.py")
_spec = importlib.util.spec_from_file_location("c_builtins",path)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Cannot load builtins.py from {path}")
c_builtins = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c_builtins)

# 掃描本地 builtins.py 中定義的函式，作為直譯器可直接呼叫的內建函式清單。
builtins_funcs = []
for name, obj in inspect.getmembers(c_builtins, inspect.isfunction):
    if obj.__module__ == c_builtins.__name__ and not name.startswith("_"):
        builtins_funcs.append(name)

# 字串相關函式需要讀寫虛擬記憶體，因此呼叫時會額外傳入 memory 物件。
str_funcs = ["memset","strlen","strcmp","strcpy","strcat","printf","puts","scanf","atoi","itoa"]

# 內建函式的 Small-C 可見簽名。
# 參數型別與格式字串細節仍保留在 builtins.py 各函式內檢查；這裡只統一檢查
# 呼叫端給的「參數數量」以及 Python 實作回傳值是否符合 Small-C 宣告型別。
# max_args=None 代表可變參數函式，例如 printf/scanf 至少要有 format string。
BUILTIN_SIGNATURES = {
    "putchar": {"return_type": "int", "min_args": 1, "max_args": 1},
    "getchar": {"return_type": "int", "min_args": 0, "max_args": 0},
    "printf": {"return_type": "void", "min_args": 1, "max_args": None},
    "puts": {"return_type": "void", "min_args": 1, "max_args": 1},
    "scanf": {"return_type": "int", "min_args": 1, "max_args": None},
    "strlen": {"return_type": "int", "min_args": 1, "max_args": 1},
    "strcpy": {"return_type": "void", "min_args": 2, "max_args": 2},
    "strcmp": {"return_type": "int", "min_args": 2, "max_args": 2},
    "strcat": {"return_type": "void", "min_args": 2, "max_args": 2},
    "abs": {"return_type": "int", "min_args": 1, "max_args": 1},
    "max": {"return_type": "int", "min_args": 2, "max_args": 2},
    "min": {"return_type": "int", "min_args": 2, "max_args": 2},
    "pow": {"return_type": "int", "min_args": 2, "max_args": 2},
    "sqrt": {"return_type": "int", "min_args": 1, "max_args": 1},
    "mod": {"return_type": "int", "min_args": 2, "max_args": 2},
    "rand": {"return_type": "int", "min_args": 0, "max_args": 0},
    "srand": {"return_type": "void", "min_args": 1, "max_args": 1},
    "memset": {"return_type": "void", "min_args": 3, "max_args": 3},
    "sizeof_int": {"return_type": "int", "min_args": 0, "max_args": 0},
    "sizeof_char": {"return_type": "int", "min_args": 0, "max_args": 0},
    "atoi": {"return_type": "int", "min_args": 1, "max_args": 1},
    "itoa": {"return_type": "void", "min_args": 2, "max_args": 2},
    "exit": {"return_type": "void", "min_args": 1, "max_args": 1},
}

NUMERIC_TYPES = {"int", "char"}
POINTER_TYPES = {"int*", "char*"}
SCALAR_TYPES = NUMERIC_TYPES | POINTER_TYPES

BUILTIN_PARAM_TYPES = {
    "putchar": ["int"],
    "getchar": [],
    "printf": ["char*", "..."],
    "puts": ["char*"],
    "scanf": ["char*", "..."],
    "strlen": ["char*"],
    "strcpy": ["char*", "char*"],
    "strcmp": ["char*", "char*"],
    "strcat": ["char*", "char*"],
    "abs": ["int"],
    "max": ["int", "int"],
    "min": ["int", "int"],
    "pow": ["int", "int"],
    "sqrt": ["int"],
    "mod": ["int", "int"],
    "rand": [],
    "srand": ["int"],
    "memset": ["char*", "int", "int"],
    "sizeof_int": [],
    "sizeof_char": [],
    "atoi": ["char*"],
    "itoa": ["int", "char*"],
    "exit": ["int"],
}


class SemanticError(Exception):
    pass


class SemanticChecker:
    def __init__(self):
        self.errors = []
        self.scopes = [{}]
        self.functions = {}
        self.current_function = None
        self.loop_depth = 0
        self.switch_depth = 0

    def error(self, line, message):
        self.errors.append(f"Error at line {line}: {message}")

    def push_scope(self):
        self.scopes.append({})

    def pop_scope(self):
        self.scopes.pop()

    def define_var(self, name, var_type, line, is_array=False, array_size=None):
        current = self.scopes[-1]
        if name in current:
            self.error(line, f"variable '{name}' is already defined in this scope.")
            return
        current[name] = {
            "type": var_type,
            "line": line,
            "is_array": is_array,
            "array_size": array_size,
        }

    def lookup_var(self, name, line):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        self.error(line, f"undefined variable '{name}'.")
        return {"type": "int", "line": line, "is_array": False, "array_size": None}

    def define_function(self, fn):
        if fn.name in self.functions:
            self.error(fn.line, f"function '{fn.name}' is already defined.")
            return
        self.functions[fn.name] = fn

    def lookup_function(self, name, line):
        if name not in self.functions and name not in BUILTIN_SIGNATURES:
            self.error(line, f"undefined function '{name}'.")
            return None
        return self.functions.get(name)

    def array_type(self, elem_type):
        return f"{elem_type}[]"

    def decay(self, value_type):
        if value_type == "int[]":
            return "int*"
        if value_type == "char[]":
            return "char*"
        return value_type

    def effective_param_type(self, param):
        if param.is_array:
            return f"{param.param_type}*"
        return param.param_type

    def is_assignable(self, target_type, value_type):
        value_type = self.decay(value_type)
        if target_type in NUMERIC_TYPES:
            return value_type in NUMERIC_TYPES
        if target_type in POINTER_TYPES:
            return value_type == target_type
        return False

    def check_assignable(self, target_type, value_type, line, context):
        if not self.is_assignable(target_type, value_type):
            self.error(line, f"cannot use value of type {value_type} as {target_type} for {context}.")

    def check(self, program):
        self.collect_function_signatures(program)
        self.check_top_level(program)
        self.check_functions()
        if not any(isinstance(node, parser.FunctionDef) and node.name == "main" for node in program):
            self.error(1, "main function not found.")
        else:
            main_fn = self.functions.get("main")
            if main_fn is not None:
                if main_fn.return_type not in ("int", "void"):
                    self.error(main_fn.line, "main function return type must be int or void.")
                if len(main_fn.params) != 0:
                    self.error(main_fn.line, "main function must not have parameters.")
        if self.errors:
            raise SemanticError("\n".join(self.errors) + f"\n{len(self.errors)} error(s) found.")

    def collect_function_signatures(self, program):
        for node in program:
            if isinstance(node, parser.FunctionDef):
                self.define_function(node)

    def check_top_level(self, program):
        for node in program:
            if isinstance(node, parser.FunctionDef):
                continue
            self.check_stmt(node)

    def check_functions(self):
        for fn in self.functions.values():
            self.current_function = fn
            self.push_scope()
            seen_params = set()
            for param in fn.params:
                param_type = self.effective_param_type(param)
                if param.name in seen_params:
                    self.error(param.line, f"parameter '{param.name}' is already defined.")
                seen_params.add(param.name)
                self.define_var(param.name, param_type, param.line)
            body_returns = self.check_stmt(fn.body)
            if fn.return_type != "void" and not body_returns:
                self.error(fn.line, f"function '{fn.name}' may end without returning {fn.return_type}.")
            self.pop_scope()
            self.current_function = None

    def check_block(self, block):
        self.push_scope()
        guaranteed_return = False
        for stmt in block.statements:
            if guaranteed_return:
                self.check_stmt(stmt)
                continue
            guaranteed_return = self.check_stmt(stmt)
        self.pop_scope()
        return guaranteed_return

    def check_statement_sequence_returns(self, statements):
        guaranteed_return = False
        for stmt in statements:
            if guaranteed_return:
                self.check_stmt(stmt)
                continue
            if isinstance(stmt, parser.BreakStmt):
                self.check_stmt(stmt)
                return False
            guaranteed_return = self.check_stmt(stmt)
        return guaranteed_return

    def check_stmt(self, node):
        if node is None or isinstance(node, parser.EmptyStmt):
            return False
        if isinstance(node, parser.Block):
            return self.check_block(node)
        if isinstance(node, parser.VarDecl):
            self.check_var_decl(node)
            return False
        if isinstance(node, parser.ExpressionStmt):
            self.expr_type(node.expr)
            return False
        if isinstance(node, parser.IfStmt):
            cond_type = self.expr_type(node.condition)
            if cond_type not in NUMERIC_TYPES:
                self.error(node.line, f"if condition must be int or char, got {cond_type}.")
            then_returns = self.check_stmt(node.then_branch)
            else_returns = self.check_stmt(node.else_branch) if node.else_branch is not None else False
            return then_returns and else_returns
        if isinstance(node, parser.WhileStmt):
            cond_type = self.expr_type(node.condition)
            if cond_type not in NUMERIC_TYPES:
                self.error(node.line, f"while condition must be int or char, got {cond_type}.")
            self.loop_depth += 1
            self.check_stmt(node.body)
            self.loop_depth -= 1
            return False
        if isinstance(node, parser.DoWhileStmt):
            self.loop_depth += 1
            self.check_stmt(node.body)
            self.loop_depth -= 1
            cond_type = self.expr_type(node.condition)
            if cond_type not in NUMERIC_TYPES:
                self.error(node.line, f"do-while condition must be int or char, got {cond_type}.")
            return False
        if isinstance(node, parser.ForStmt):
            self.push_scope()
            if node.init is not None:
                if isinstance(node.init, (parser.VarDecl, parser.ExpressionStmt, parser.EmptyStmt)):
                    self.check_stmt(node.init)
                else:
                    self.expr_type(node.init)
            if node.condition is not None:
                cond_type = self.expr_type(node.condition)
                if cond_type not in NUMERIC_TYPES:
                    self.error(node.line, f"for condition must be int or char, got {cond_type}.")
            if node.update is not None:
                self.expr_type(node.update)
            self.loop_depth += 1
            self.check_stmt(node.body)
            self.loop_depth -= 1
            self.pop_scope()
            return False
        if isinstance(node, parser.SwitchStmt):
            expr_type = self.expr_type(node.expr)
            if expr_type not in NUMERIC_TYPES:
                self.error(node.line, f"switch expression must be int or char, got {expr_type}.")
            self.switch_depth += 1
            self.push_scope()
            has_default = False
            all_clauses_return = True
            for clause in node.clauses:
                if clause.is_default:
                    has_default = True
                if not self.check_statement_sequence_returns(clause.statements):
                    all_clauses_return = False
            self.pop_scope()
            self.switch_depth -= 1
            return has_default and all_clauses_return
        if isinstance(node, parser.BreakStmt):
            if self.loop_depth == 0 and self.switch_depth == 0:
                self.error(node.line, "break statement is only allowed inside a loop or switch.")
            return False
        if isinstance(node, parser.ContinueStmt):
            if self.loop_depth == 0:
                self.error(node.line, "continue statement is only allowed inside a loop.")
            return False
        if isinstance(node, parser.ReturnStmt):
            self.check_return(node)
            return True
        self.error(getattr(node, "line", 1), f"unsupported statement type {type(node).__name__}.")
        return False

    def check_var_decl(self, node):
        if node.is_array:
            if node.var_type not in ("int", "char"):
                self.error(node.line, f"array element type {node.var_type} is not supported.")
            if node.array_size is None or node.array_size <= 0:
                self.error(node.line, f"array '{node.name}' length must be greater than 0.")
            if isinstance(node.init_expr, parser.String):
                if node.var_type != "char":
                    self.error(node.line, "string initializer is only valid for char arrays.")
                if node.array_size is not None and len(node.init_expr.value) + 1 > node.array_size:
                    self.error(node.line, f"string initializer for '{node.name}' is larger than array size.")
            elif isinstance(node.init_expr, parser.InitList):
                for index, value in enumerate(node.init_expr.values):
                    value_type = self.expr_type(value)
                    if value_type not in NUMERIC_TYPES:
                        self.error(node.line, f"array '{node.name}' element {index} cannot be initialized with {value_type}.")
            elif node.init_expr is not None:
                self.error(node.line, f"array '{node.name}' initializer must be a string or initializer list.")
            self.define_var(node.name, node.var_type, node.line, is_array=True, array_size=node.array_size)
            return

        if node.var_type not in SCALAR_TYPES:
            self.error(node.line, f"unsupported variable type {node.var_type}.")
        if node.init_expr is not None:
            init_type = self.expr_type(node.init_expr)
            self.check_assignable(node.var_type, init_type, node.line, f"initializer of '{node.name}'")
        self.define_var(node.name, node.var_type, node.line)

    def check_return(self, node):
        if self.current_function is None:
            self.error(node.line, "return statement is only allowed inside a function.")
            return
        expected = self.current_function.return_type
        if node.expr is None:
            if expected != "void":
                self.error(node.line, f"function '{self.current_function.name}' must return {expected}.")
            return
        value_type = self.expr_type(node.expr)
        if expected == "void":
            self.error(node.line, f"void function '{self.current_function.name}' should not return a value.")
            return
        self.check_assignable(expected, value_type, node.line, f"return from '{self.current_function.name}'")

    def lvalue_type(self, expr):
        if isinstance(expr, parser.Identifier):
            symbol = self.lookup_var(expr.name, expr.line)
            if symbol["is_array"]:
                self.error(expr.line, f"cannot assign to array '{expr.name}'.")
            return symbol["type"]
        if isinstance(expr, parser.IndexExpr):
            if isinstance(expr.base, parser.String):
                self.error(expr.line, "cannot assign to string literal.")
            base_type = self.expr_type(expr.base)
            index_type = self.expr_type(expr.index)
            if index_type not in NUMERIC_TYPES:
                self.error(expr.line, f"array index must be int or char, got {index_type}.")
            decayed = self.decay(base_type)
            if decayed == "int*":
                return "int"
            if decayed == "char*":
                return "char"
            self.error(expr.line, f"cannot apply index operator to {base_type}.")
            return "int"
        if isinstance(expr, parser.UnaryExpr) and expr.operator == "*":
            ptr_type = self.expr_type(expr.operand)
            if ptr_type == "int*":
                return "int"
            if ptr_type == "char*":
                return "char"
            self.error(expr.line, f"cannot apply unary '*' to non-pointer expression of type {ptr_type}.")
            return "int"
        self.error(getattr(expr, "line", 1), "left side of assignment must be a modifiable lvalue.")
        return "int"

    def expr_type(self, expr):
        if isinstance(expr, parser.Number):
            return "int"
        if isinstance(expr, parser.Char):
            return "char"
        if isinstance(expr, parser.String):
            return "char[]"
        if isinstance(expr, parser.Identifier):
            symbol = self.lookup_var(expr.name, expr.line)
            if symbol["is_array"]:
                return self.array_type(symbol["type"])
            return symbol["type"]
        if isinstance(expr, parser.InitList):
            self.error(expr.line, "initializer list is only valid in array declarations.")
            return "int"
        if isinstance(expr, parser.IndexExpr):
            base_type = self.expr_type(expr.base)
            index_type = self.expr_type(expr.index)
            if index_type not in NUMERIC_TYPES:
                self.error(expr.line, f"array index must be int or char, got {index_type}.")
            decayed = self.decay(base_type)
            if decayed == "int*":
                return "int"
            if decayed == "char*":
                return "char"
            self.error(expr.line, f"cannot apply index operator to {base_type}.")
            return "int"
        if isinstance(expr, parser.UnaryExpr):
            return self.unary_type(expr)
        if isinstance(expr, parser.BinaryExpr):
            return self.binary_type(expr)
        if isinstance(expr, parser.AssignmentExpr):
            target_type = self.lvalue_type(expr.left)
            right_type = self.expr_type(expr.right)
            if expr.operator == "=":
                self.check_assignable(target_type, right_type, expr.line, "assignment")
                return target_type
            if expr.operator in ("+=", "-="):
                decayed_target = self.decay(target_type)
                if decayed_target in POINTER_TYPES and right_type in NUMERIC_TYPES:
                    return target_type
                if target_type in NUMERIC_TYPES and right_type in NUMERIC_TYPES:
                    return target_type
                self.error(expr.line, f"cannot apply operator '{expr.operator}' to {target_type} and {right_type}.")
                return target_type
            if expr.operator in ("*=", "/=", "%="):
                if target_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                    self.error(expr.line, f"cannot apply operator '{expr.operator}' to {target_type} and {right_type}.")
                return target_type
            self.error(expr.line, f"unsupported assignment operator '{expr.operator}'.")
            return target_type
        if isinstance(expr, parser.CallExpr):
            return self.call_type(expr)
        self.error(getattr(expr, "line", 1), f"unsupported expression type {type(expr).__name__}.")
        return "int"

    def unary_type(self, expr):
        operand_type = self.expr_type(expr.operand)
        if expr.operator in ("+", "-", "!", "~"):
            if operand_type not in NUMERIC_TYPES:
                self.error(expr.line, f"cannot apply unary '{expr.operator}' to {operand_type}.")
            return "int"
        if expr.operator == "&":
            if isinstance(expr.operand, parser.Identifier):
                symbol = self.lookup_var(expr.operand.name, expr.line)
                if symbol["is_array"]:
                    self.error(expr.line, f"cannot apply unary '&' to array '{expr.operand.name}'.")
                    return f"{symbol['type']}*"
                if symbol["type"] in POINTER_TYPES:
                    self.error(expr.line, f"cannot apply unary '&' to pointer variable '{expr.operand.name}'.")
                    return symbol["type"]
                return f"{symbol['type']}*"
            if isinstance(expr.operand, parser.IndexExpr):
                target_type = self.lvalue_type(expr.operand)
                return f"{target_type}*"
            self.error(expr.line, "cannot apply unary '&' to non-variable.")
            return "int*"
        if expr.operator == "*":
            decayed = self.decay(operand_type)
            if decayed == "int*":
                return "int"
            if decayed == "char*":
                return "char"
            self.error(expr.line, f"cannot apply unary '*' to non-pointer expression of type {operand_type}.")
            return "int"
        if expr.operator in ("++", "--"):
            target_type = self.lvalue_type(expr.operand)
            if target_type not in SCALAR_TYPES:
                self.error(expr.line, f"cannot apply unary '{expr.operator}' to {target_type}.")
            return target_type
        self.error(expr.line, f"unsupported unary operator '{expr.operator}'.")
        return "int"

    def binary_type(self, expr):
        left_type = self.expr_type(expr.left)
        right_type = self.expr_type(expr.right)
        if expr.operator in ("&&", "||"):
            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                self.error(expr.line, f"cannot apply operator '{expr.operator}' to {left_type} and {right_type}.")
            return "int"
        if expr.operator == "+":
            left_decayed = self.decay(left_type)
            right_decayed = self.decay(right_type)
            if left_type in NUMERIC_TYPES and right_type in NUMERIC_TYPES:
                return "int"
            if left_decayed in POINTER_TYPES and right_type in NUMERIC_TYPES:
                return left_decayed
            if left_type in NUMERIC_TYPES and right_decayed in POINTER_TYPES:
                return right_decayed
            self.error(expr.line, f"cannot apply operator '+' to {left_type} and {right_type}.")
            return "int"
        if expr.operator == "-":
            left_decayed = self.decay(left_type)
            right_decayed = self.decay(right_type)
            if left_type in NUMERIC_TYPES and right_type in NUMERIC_TYPES:
                return "int"
            if left_decayed in POINTER_TYPES and right_type in NUMERIC_TYPES:
                return left_decayed
            if left_decayed == right_decayed and left_decayed in POINTER_TYPES:
                return "int"
            self.error(expr.line, f"cannot apply operator '-' to {left_type} and {right_type}.")
            return "int"
        if expr.operator in ("*", "/", "%", "&", "|", "^", "<<", ">>", "<", "<=", ">", ">=", "==", "!="):
            if left_type not in NUMERIC_TYPES or right_type not in NUMERIC_TYPES:
                self.error(expr.line, f"cannot apply operator '{expr.operator}' to {left_type} and {right_type}.")
            return "int"
        self.error(expr.line, f"unsupported binary operator '{expr.operator}'.")
        return "int"

    def call_type(self, expr):
        if not isinstance(expr.fn, parser.Identifier):
            self.error(expr.line, "function name must be an identifier.")
            return "int"
        name = expr.fn.name
        arg_types = [self.decay(self.expr_type(arg)) for arg in expr.args]
        if name in BUILTIN_SIGNATURES:
            signature = BUILTIN_SIGNATURES[name]
            min_args = signature["min_args"]
            max_args = signature["max_args"]
            if len(arg_types) < min_args or (max_args is not None and len(arg_types) > max_args):
                expected = f"at least {min_args}" if max_args is None else str(min_args)
                self.error(expr.line, f"function '{name}' expects {expected} arguments, got {len(arg_types)}.")
            expected_types = BUILTIN_PARAM_TYPES.get(name, [])
            for index, expected_type in enumerate(expected_types):
                if expected_type == "...":
                    break
                if index < len(arg_types):
                    self.check_assignable(expected_type, arg_types[index], expr.line, f"parameter {index + 1} of '{name}'")
            return signature["return_type"]

        fn = self.lookup_function(name, expr.line)
        if fn is None:
            return "int"
        if len(arg_types) != len(fn.params):
            self.error(expr.line, f"function '{name}' expects {len(fn.params)} arguments, got {len(arg_types)}.")
        for index, (arg_type, param) in enumerate(zip(arg_types, fn.params)):
            param_type = self.effective_param_type(param)
            self.check_assignable(param_type, arg_type, expr.line, f"parameter {index + 1} '{param.name}' of '{name}'")
        return fn.return_type


def check_semantics(program):
    SemanticChecker().check(program)

# break / continue 可能出現在巢狀 block 或 if 裡，
# 用內部 signal 往外傳遞，直到最近的迴圈節點接住。
class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class ExitSignal(Exception):
    def __init__(self, code, line):
        self.code = code
        self.line = line

class ReturnSignal(Exception):
    """函式內 return 用的控制流程訊號，攜帶回傳值往外層 CallExpr 傳遞。"""
    def __init__(self, value, line):
        self.value = value
        self.line = line

class Interpreter:
    """執行 AST 的狀態容器。"""

    def __init__(self):
        # 保存目前執行環境的虛擬記憶體與符號表，後續求值時會用來查變數、地址與函式。
        self.memory: memory.VirtualMemory = memory.VirtualMemory()
        self.symtable: symtable.symtable = symtable.symtable()
        self.trace_enabled = False # 之後實作 TRACE 指令時會用到
        # RUN 會填入「原始程式行號 -> 原始碼文字」，TRACE 才能印出使用者看得到的語句。
        self.trace_source_lines: dict[int, str] = {}
        self._rng = random.Random(1)
        self.randseed = 1

    def is_traceable_statement(self, ast_node) -> bool:
        """判斷 AST 節點是否代表一個可執行語句，而不是 expression 內部節點。"""
        return isinstance(ast_node, (
            parser.VarDecl,
            parser.ExpressionStmt,
            parser.IfStmt,
            parser.WhileStmt,
            parser.DoWhileStmt,
            parser.ForStmt,
            parser.SwitchStmt,
            parser.BreakStmt,
            parser.ContinueStmt,
            parser.ReturnStmt,
            parser.EmptyStmt,
        ))

    def trace_statement(self, ast_node) -> None:
        """TRACE ON 時，在執行 statement 前顯示來源行號與原始程式碼。"""
        if not self.trace_enabled or not self.trace_source_lines:
            return
        if not self.is_traceable_statement(ast_node):
            return

        line = getattr(ast_node, "line", None)
        if line is None:
            return
        source = self.trace_source_lines.get(line, "").strip()
        if source == "":
            source = repr(ast_node)
        print(f"[line {line}] {source}")

    def decay_array_value(self, value):
        """將 expression 中的陣列值轉成首元素指標，對應 C 的 array-to-pointer decay。"""
        # 不是陣列的值不需要轉換，例如 int、int_ptr、char_ptr 都直接保留原值。
        if not isinstance(value, array):
            return value
        # int arr[] 在 expression / argument / pointer assignment 中退化成 int*，指向 arr[0]。
        if value.elem_type == "int":
            return int_ptr(value.addr)
        # char array 與 string literal 都用 array(..., "char") 表示，因此會退化成 char*。
        if value.elem_type == "char":
            return char_ptr(value.addr)
        # 目前專案不支援 pointer array 等其他元素型別，避免靜默轉成錯誤 pointer。
        raise Exception(f"Runtime error: Unsupported array element type {value.elem_type}.")

    def resolve_lvalue(self, expr):
        """解析可寫入的左值 expression，回傳 (addr, type)。"""
        if isinstance(expr, parser.Identifier):
            # 變數本身是最基本的左值；陣列名稱只會 decay 成 pointer，不能被整體指定。
            var_info = self.symtable.lookup_var(expr.name)
            if var_info.is_array:
                raise Exception(f"Runtime error: Cannot assign to array '{expr.name}' at line {expr.line}.")
            return var_info.addr, var_info.var_type

        if isinstance(expr, parser.IndexExpr):
            # 字串常數雖然可讀取索引值，但不作為可寫左值，避免修改 literal 內容。
            if isinstance(expr.base, parser.String):
                raise Exception(f"Runtime error: Cannot assign to string literal at line {expr.line}.")
            base_val = self.evaluate(expr.base)
            index = self.evaluate(expr.index)
            if not isinstance(index, int):
                raise Exception(f"Runtime error: Array index must be int at line {expr.line}.")
            if isinstance(base_val, array):
                # arr[i]：已知 allocation 起點，直接以陣列邊界檢查取得元素地址。
                element_size = symtable.sizeof_type(base_val.elem_type)
                target_addr = base_val.addr + index * element_size
                self.memory.check_bounds(base_val.addr, target_addr, element_size)
                return target_addr, base_val.elem_type
            if isinstance(base_val, int_ptr):
                # p[i] 等同 *(p + i)，ptr_add() 會依 int stride 位移並檢查 allocation。
                target_addr = self.memory.ptr_add(base_val.addr, index, "int")
                self.memory.check_ptr(target_addr, 4)
                return target_addr, "int"
            if isinstance(base_val, char_ptr):
                # char* 的索引以 1 byte 為 stride，回傳的左值型別是 char。
                target_addr = self.memory.ptr_add(base_val.addr, index, "char")
                self.memory.check_ptr(target_addr, 1)
                return target_addr, "char"
            raise Exception(f"Runtime error: Cannot apply index operator to {type_mapping[type(base_val).__name__]} at line {expr.line}.")

        if isinstance(expr, parser.UnaryExpr) and expr.operator == "*":
            # *p 作為左值時，寫入位置就是 p 目前指向的地址。
            ptr = self.evaluate(expr.operand) # 先求 operand 的值，確認是指標後回傳地址與型別。
            if isinstance(ptr, int_ptr):
                self.memory.check_ptr(ptr.addr, 4)
                return ptr.addr, "int"
            if isinstance(ptr, char_ptr):
                self.memory.check_ptr(ptr.addr, 1)
                return ptr.addr, "char"
            raise Exception(f"Runtime error: Cannot apply unary '*' to non-pointer expression at line {expr.line}.")

        raise Exception(f"Runtime error: Left side of assignment must be a modifiable lvalue at line {expr.line}.")

    def read_lvalue(self, addr, value_type):
        """依左值型別從記憶體讀出目前值。"""
        # 複合指定需要先讀舊值，例如 arr[i] += 1 或 *p -= 2。
        if value_type == "int":
            return self.memory.get_int(addr)
        if value_type == "char":
            return self.memory.get_char(addr)
        if value_type == "int*":
            return int_ptr(self.memory.get_ptr(addr))
        if value_type == "char*":
            return char_ptr(self.memory.get_ptr(addr))
        raise Exception(f"Runtime error: Unsupported lvalue type {value_type}.")

    def write_lvalue(self, addr, value_type, value, line):
        """依左值型別寫入新值，並在 pointer 指定時維持型別安全。"""
        # 寫入集中在這裡處理，讓 x、arr[i]、p[i]、*p 共用同一套型別檢查。
        if value_type == "int":
            if not isinstance(value, int):
                raise Exception(f"Runtime error: Cannot assign value of type {type_mapping[type(value).__name__]} to int at line {line}.")
            self.memory.set_int(addr, value)
            return
        if value_type == "char":
            if not isinstance(value, int):
                raise Exception(f"Runtime error: Cannot assign value of type {type_mapping[type(value).__name__]} to char at line {line}.")
            self.memory.set_char(addr, value)
            return
        if value_type == "int*":
            # pointer 左值可接受同型 pointer；array 右值先 decay 成首元素 pointer。
            value = self.decay_array_value(value)
            if isinstance(value, int):
                raise Exception(f"Runtime error: Cannot assign integer value {value} to int* at line {line}.")
            if not isinstance(value, int_ptr):
                raise Exception(f"Runtime error: Cannot assign value of type {type_mapping[type(value).__name__]} to int* at line {line}.")
            self.memory.set_ptr(addr, value.addr)
            return
        if value_type == "char*":
            # char array 與 string literal 都會透過 decay_array_value() 轉成 char_ptr。
            value = self.decay_array_value(value)
            if isinstance(value, int):
                raise Exception(f"Runtime error: Cannot assign integer value {value} to char* at line {line}.")
            if not isinstance(value, char_ptr):
                raise Exception(f"Runtime error: Cannot assign value of type {type_mapping[type(value).__name__]} to char* at line {line}.")
            self.memory.set_ptr(addr, value.addr)
            return
        raise Exception(f"Runtime error: Unsupported lvalue type {value_type} at line {line}.")

    def alloc_for_current_scope(self, size: int) -> int:
        """全域宣告配置在 global 區；函式 scope 內的變數配置在 stack frame。"""
        if self.symtable.current_scope_level() == 0:
            return self.memory.alloc_global(size)
        return self.memory.alloc_stack(size)

    def effective_param_type(self, param):
        """陣列參數在 C 中會退化成指標參數，例如 int a[] 視為 int*。"""
        if param.is_array:
            base_type = param.param_type if hasattr(param, "param_type") else param.var_type
            if base_type.endswith("*"):
                raise Exception(f"Runtime error: Pointer array parameter '{param.name}' is not supported at line {getattr(param, 'line', '?')}.")
            return base_type + "*"
        return param.param_type if hasattr(param, "param_type") else param.var_type

    def validate_value_for_type(self, value, expected_type: str, line: int, context: str):
        """檢查值是否可用於指定型別；pointer 目標會先套用 array-to-pointer decay。"""
        if expected_type in ("int*", "char*"):
            value = self.decay_array_value(value)
        valid = (
            (expected_type == "int" and isinstance(value, int))
            or (expected_type == "char" and isinstance(value, int))
            or (expected_type == "int*" and isinstance(value, int_ptr))
            or (expected_type == "char*" and isinstance(value, char_ptr))
            or (expected_type == "void" and value is None)
        )
        if not valid:
            raise Exception(f"Runtime error: Cannot use value of type {type_mapping[type(value).__name__]} as {expected_type} for {context} at line {line}.")
        return value

    def validate_argument_count(self, function_name: str, min_args: int, max_args: int | None, got_args: int, line: int):
        """統一檢查函式參數數量；型別細節由呼叫端或 builtins.py 各自處理。"""
        if max_args is None:
            # variadic 函式只要求固定參數數量下限，例如 printf(fmt, ...)。
            if got_args < min_args:
                raise Exception(f"Runtime error: Function '{function_name}' expects at least {min_args} arguments, got {got_args} at line {line}.")
            return
        if min_args == max_args:
            if got_args != min_args:
                raise Exception(f"Runtime error: Function '{function_name}' expects {min_args} arguments, got {got_args} at line {line}.")
            return
        if got_args < min_args or got_args > max_args:
            raise Exception(f"Runtime error: Function '{function_name}' expects between {min_args} and {max_args} arguments, got {got_args} at line {line}.")

    def validate_return_value(self, function_name: str, expected_type: str, value, line: int):
        """統一檢查自訂函式與內建函式的回傳值是否符合宣告型別。"""
        if expected_type == "void":
            if value is not None:
                raise Exception(f"Runtime error: Void function '{function_name}' should not return a value at line {line}.")
            return None
        if value is None:
            raise Exception(f"Runtime error: Function '{function_name}' must return {expected_type} at line {line}.")
        return self.validate_value_for_type(value, expected_type, line, f"return from '{function_name}'")

    def call_builtin_function(self, function_name: str, arg_values: list, line: int):
        """呼叫內建函式，外層只檢查參數數量與 return type，保留 builtins.py 的型別檢查。"""
        signature = BUILTIN_SIGNATURES.get(function_name)
        if signature is None:
            raise Exception(f"Runtime error: Missing built-in signature for '{function_name}' at line {line}.")

        self.validate_argument_count(function_name, signature["min_args"], signature["max_args"], len(arg_values), line)

        if function_name == "exit":
            code = arg_values[0]
            if type(code) is not int:
                got_type = type_mapping.get(type(code).__name__, type(code).__name__)
                raise Exception(f"Runtime error: exit expects int, got {got_type} at line {line}.")
            raise ExitSignal(code, line)

        builtin_func = getattr(c_builtins, function_name)
        if function_name == "rand":
            return_value = builtin_func(self._rng)
        elif function_name == "srand":
            # seed 的型別仍由 builtins.srand() 檢查；成功後才同步記錄目前 seed。
            return_value = builtin_func(self._rng, *arg_values)
            self.randseed = arg_values[0]
        elif function_name in str_funcs:
            return_value = builtin_func(self.memory, *arg_values)
        else:
            return_value = builtin_func(*arg_values)

        return self.validate_return_value(function_name, signature["return_type"], return_value, line)

    def call_user_function(self, function_name: str, arg_values: list, line: int):
        """呼叫使用者定義函式：建立參數 scope、執行 body，並處理 return 值。"""
        # 從函式表取得先前由 FunctionDef 註冊的簽名與 body。
        func = self.symtable.lookup_function(function_name)
        self.validate_argument_count(function_name, len(func.params), len(func.params), len(arg_values), line)

        # 記住呼叫前 stack_top，函式返回時會釋放本次呼叫配置的所有參數與區域變數。
        frame_entry_top = self.memory.stack_top
        self.symtable.push_scope()
        try:
            for param, arg_value in zip(func.params, arg_values):
                param_type = self.effective_param_type(param)
                # 參數先做型別檢查；陣列實參已在 CallExpr 階段 decay 成對應 pointer。
                arg_value = self.validate_value_for_type(arg_value, param_type, line, f"parameter '{param.name}'")
                # 每個參數都配置成目前函式 scope 內的一個 stack 變數，後續可被直接讀寫。
                addr = self.memory.alloc_stack(symtable.sizeof_type(param_type))
                self.symtable.define_var(param.name, param_type, addr, line)
                self.write_lvalue(addr, param_type, arg_value, line)

            try:
                # 函式呼叫本身已經建立 function scope，參數也在同一層 scope。
                # 因此函式最外層 body 不走 Block 分支，避免額外建立一層 scope
                # 造成區域變數可以錯誤地遮蔽同名參數。
                for stmt in func.body.statements:
                    self.evaluate(stmt)
            except ReturnSignal as signal:
                # 非 void 函式要檢查 return value 是否符合宣告回傳型別；void 函式則不可回傳值。
                return self.validate_return_value(function_name, func.return_type, signal.value, signal.line)

            if func.return_type != "void":
                raise Exception(f"Runtime error: Function '{function_name}' ended without returning {func.return_type} at line {line}.")
            return None
        finally:
            # 無論正常 return 或執行期錯誤，都必須復原 scope 與 stack frame，避免污染後續 REPL 狀態。
            self.symtable.pop_scope()
            self.memory.free_stack_frame(frame_entry_top)

    def evaluate(self, ast_node):
        # 根據 AST 節點型別遞迴求值，回傳此節點在目前執行環境中的值。
        self.trace_statement(ast_node)
        if isinstance(ast_node, parser.Number):
            # 數字常數直接回傳原值，不需要額外查表。
            return ast_node.value
        elif isinstance(ast_node, parser.Char):
            # 字元常數在 AST 中已經是單一值，直接回傳其 ASCII 值。
            return ord(ast_node.value)
        elif isinstance(ast_node, parser.String):
            # 字串常數先配置到虛擬記憶體，再回傳起始位址。
            return array(self.memory.set_string(ast_node.value), len(ast_node.value)+1, 'char') #放進記憶體並回傳地址 （包含結尾的 \0 字元）
        elif isinstance(ast_node, parser.UnaryExpr):
            # 一元運算依 operator 決定是否需要先取 operand 的值。
            if ast_node.operator == "+":
                val = self.evaluate(ast_node.operand)
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '+' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return val
            elif ast_node.operator == "-":
                val = self.evaluate(ast_node.operand)
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '-' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return -val
            elif ast_node.operator == "!":
                val = self.evaluate(ast_node.operand)
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '!' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return int(not val)
            elif ast_node.operator == "~":
                val = self.evaluate(ast_node.operand)
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '~' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return ~val
            elif ast_node.operator == "&":
                if isinstance(ast_node.operand, parser.Identifier):
                    var_info = self.symtable.lookup_var(ast_node.operand.name)
                    if var_info.is_array:
                        raise Exception(f"Runtime error: Cannot apply unary '&' to array '{ast_node.operand.name}'; use '{ast_node.operand.name}' or '&{ast_node.operand.name}[0]' at line {ast_node.line}.")
                    if var_info.var_type == "int":
                        return int_ptr(var_info.addr)
                    elif var_info.var_type == "char":
                        return char_ptr(var_info.addr)
                    elif var_info.var_type == "int*" or var_info.var_type == "char*":
                        raise Exception(f"Runtime error: Cannot apply unary '&' to pointer variable '{ast_node.operand.name}' at line {ast_node.line}.")
                    else:
                        raise Exception(f"Runtime error: Unsupported variable type {var_info.var_type} for variable '{ast_node.operand.name}' at line {ast_node.line}.")
                elif isinstance(ast_node.operand, parser.IndexExpr):
                    target_addr, target_type = self.resolve_lvalue(ast_node.operand)
                    if target_type == "int":
                        return int_ptr(target_addr)
                    elif target_type == "char":
                        return char_ptr(target_addr)
                    else:
                        raise Exception(f"Runtime error: Cannot take address of {target_type} expression at line {ast_node.line}.")
                else:
                    raise Exception(f"Runtime error: Cannot apply unary '&' to non-variable at line {ast_node.line}.")
            elif ast_node.operator == "*":
                ptr = self.evaluate(ast_node.operand)
                if not isinstance(ptr, (int_ptr, char_ptr)):
                    raise Exception(f"Runtime error: Cannot apply unary '*' to non-pointer expression at line {ast_node.line}.")
                if isinstance(ptr, int_ptr):
                    self.memory.check_ptr(ptr.addr,4) # 是否為有效指標（非 null pointer，且不越界）
                    return self.memory.get_int(ptr.addr)
                elif isinstance(ptr, char_ptr):
                    self.memory.check_ptr(ptr.addr,1) # 是否為有效指標（非 null pointer，且不越界）
                    return self.memory.get_char(ptr.addr)
            elif ast_node.operator == "++" and ast_node.postfix == False:
                if not isinstance(ast_node.operand, parser.Identifier):
                    raise Exception(f"Runtime error: Cannot apply unary '++' to non-variable at line {ast_node.line}.")
                var_info = self.symtable.lookup_var(ast_node.operand.name)
                old_val=0
                if var_info.var_type == 'int':
                    old_val = self.memory.get_int(var_info.addr)
                    self.memory.set_int(var_info.addr, old_val + 1)
                elif var_info.var_type == 'char':
                    old_val = self.memory.get_char(var_info.addr)
                    self.memory.set_char(var_info.addr, old_val + 1)
                elif var_info.var_type == 'int*':
                    old_addr = self.memory.get_ptr(var_info.addr) # 取得目前指標值
                    new_addr = self.memory.ptr_add(old_addr, 1, "int") # 指標運算：假設是 int*，每次加 1 就加 4 bytes
                    self.memory.set_ptr(var_info.addr, new_addr)
                    return int_ptr(new_addr) # 回傳加 4 後的指標值
                elif var_info.var_type == 'char*':
                    old_addr = self.memory.get_ptr(var_info.addr) # 取得目前指標值
                    new_addr = self.memory.ptr_add(old_addr, 1, "char") # 指標運算：char* 加 1 實際上地址加 1
                    self.memory.set_ptr(var_info.addr, new_addr)
                    return char_ptr(new_addr) # 回傳加 1 後的指標值
                else:
                    raise Exception(f"Runtime error: Unsupported variable type {var_info.var_type} for variable '{ast_node.operand.name}' at line {ast_node.line}.")
                return old_val + 1
            elif ast_node.operator == "--" and ast_node.postfix == False:
                if not isinstance(ast_node.operand, parser.Identifier):
                    raise Exception(f"Runtime error: Cannot apply unary '--' to non-variable at line {ast_node.line}.")
                var_info = self.symtable.lookup_var(ast_node.operand.name)
                old_val=0
                if var_info.var_type == 'int':
                    old_val = self.memory.get_int(var_info.addr)
                    self.memory.set_int(var_info.addr, old_val - 1)
                    return old_val - 1
                elif var_info.var_type == 'char':
                    old_val = self.memory.get_char(var_info.addr)
                    self.memory.set_char(var_info.addr, old_val - 1)
                    return old_val - 1
                elif var_info.var_type == 'int*':
                    old_addr = self.memory.get_ptr(var_info.addr) # 取得目前指標值
                    new_addr = self.memory.ptr_add(old_addr, -1, "int") # 指標運算：int*，每次減 1 就減 4 bytes
                    self.memory.set_ptr(var_info.addr, new_addr)
                    return int_ptr(new_addr) # 回傳減 4 後的指標值
                elif var_info.var_type == 'char*':
                    old_addr = self.memory.get_ptr(var_info.addr) # 取得目前指標值
                    new_addr = self.memory.ptr_add(old_addr, -1, "char") # 指標運算：char* 減 1 實際上地址減 1
                    self.memory.set_ptr(var_info.addr, new_addr)
                    return char_ptr(new_addr) # 回傳減 1 後的指標值
                else:
                    raise Exception(f"Runtime error: Unsupported variable type {var_info.var_type} for variable '{ast_node.operand.name}' at line {ast_node.line}.")
                
                
                
        elif isinstance(ast_node, parser.BinaryExpr):
            # 二元運算採延遲求值：先求左子表達式，
            # 對於 && / || 採短路（必要時才求右子表達式），其餘運算再求右子表達式。
            left_val = self.evaluate(ast_node.left)
            if ast_node.operator == "&&":
                if not isinstance(left_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '&&' to {type_mapping[type(left_val).__name__]} and <right> at line {ast_node.line}.")
                if not left_val:
                    return 0
                right_val = self.evaluate(ast_node.right)
                if not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '&&' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return 1 if left_val and right_val else 0
            elif ast_node.operator == "||":
                if not isinstance(left_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '||' to {type_mapping[type(left_val).__name__]} and <right> at line {ast_node.line}.")
                if left_val:
                    return 1
                right_val = self.evaluate(ast_node.right)
                if not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '||' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return 1 if left_val or right_val else 0
            # 非短路運算再求右子表達式
            right_val = self.evaluate(ast_node.right)
            if ast_node.operator in ("+", "-"):
                # 陣列在加減運算中 decay 成首元素指標，例如 arr + 1 等同 &arr[0] + 1。
                left_val = self.decay_array_value(left_val)
                right_val = self.decay_array_value(right_val)
            if ast_node.operator == "+":
                if isinstance(left_val, int) and isinstance(right_val, int):
                    return left_val + right_val
                # 指標加整數會依 pointed type 做 stride：int* 每格 4 bytes，char* 每格 1 byte。
                if isinstance(left_val, int_ptr) and isinstance(right_val, int):
                    return int_ptr(self.memory.ptr_add(left_val.addr, right_val, "int"))
                if isinstance(left_val, char_ptr) and isinstance(right_val, int):
                    return char_ptr(self.memory.ptr_add(left_val.addr, right_val, "char"))
                # C 允許整數放在左邊，例如 2 + p，語意同 p + 2。
                if isinstance(left_val, int) and isinstance(right_val, int_ptr):
                    return int_ptr(self.memory.ptr_add(right_val.addr, left_val, "int"))
                if isinstance(left_val, int) and isinstance(right_val, char_ptr):
                    return char_ptr(self.memory.ptr_add(right_val.addr, left_val, "char"))
                raise Exception(f"Runtime error: Cannot apply operator '+' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
            elif ast_node.operator == "-":
                if isinstance(left_val, int) and isinstance(right_val, int):
                    return left_val - right_val
                # ptr - int 回傳同型指標，offset 轉成負值後交給 ptr_add() 做 stride 與邊界檢查。
                if isinstance(left_val, int_ptr) and isinstance(right_val, int):
                    return int_ptr(self.memory.ptr_add(left_val.addr, -right_val, "int"))
                if isinstance(left_val, char_ptr) and isinstance(right_val, int):
                    return char_ptr(self.memory.ptr_add(left_val.addr, -right_val, "char"))
                # ptr - ptr 回傳元素距離，不是 byte 距離；兩個指標必須同型且位於同一 allocation。
                if isinstance(left_val, int_ptr) and isinstance(right_val, int_ptr):
                    left_alloc = self.memory.find_allocation(left_val.addr)
                    right_alloc = self.memory.find_allocation(right_val.addr)
                    if left_alloc is None or right_alloc is None:
                        raise Exception(f"Runtime error: Cannot subtract invalid int* pointers at line {ast_node.line}.")
                    if left_alloc != right_alloc:
                        raise Exception(f"Runtime error: Cannot subtract int* pointers from different allocations at line {ast_node.line}.")
                    byte_diff = left_val.addr - right_val.addr
                    if byte_diff % 4 != 0:
                        raise Exception(f"Runtime error: Cannot subtract unaligned int* pointers at line {ast_node.line}.")
                    return byte_diff // 4
                if isinstance(left_val, char_ptr) and isinstance(right_val, char_ptr):
                    left_alloc = self.memory.find_allocation(left_val.addr)
                    right_alloc = self.memory.find_allocation(right_val.addr)
                    if left_alloc is None or right_alloc is None:
                        raise Exception(f"Runtime error: Cannot subtract invalid char* pointers at line {ast_node.line}.")
                    if left_alloc != right_alloc:
                        raise Exception(f"Runtime error: Cannot subtract char* pointers from different allocations at line {ast_node.line}.")
                    return left_val.addr - right_val.addr
                raise Exception(f"Runtime error: Cannot apply operator '-' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
            elif ast_node.operator == "*":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '*' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val * right_val
            elif ast_node.operator == "/":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '/' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                if right_val == 0:
                    raise Exception(f"Runtime error: Division by zero at line {ast_node.line}.")
                return c_div(left_val, right_val)
            elif ast_node.operator == "%":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '%' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                if right_val == 0:
                    raise Exception(f"Runtime error: Modulo by zero at line {ast_node.line}.")
                return c_mod(left_val, right_val)
            elif ast_node.operator == "&":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '&' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val & right_val
            elif ast_node.operator == "|":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '|' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val | right_val
            elif ast_node.operator == "^":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '^' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val ^ right_val
            elif ast_node.operator == "<<":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '<<' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val << right_val
            elif ast_node.operator == ">>":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '>>' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val >> right_val
            elif ast_node.operator == "==":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '==' at line {ast_node.line}.")
                return 1 if left_val == right_val else 0
            elif ast_node.operator == "!=":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '!=' at line {ast_node.line}.")
                return 1 if left_val != right_val else 0
            elif ast_node.operator == "<":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '<' at line {ast_node.line}.")
                return 1 if left_val < right_val else 0
            elif ast_node.operator == "<=":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '<=' at line {ast_node.line}.")
                return 1 if left_val <= right_val else 0
            elif ast_node.operator == ">":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '>' at line {ast_node.line}.")
                return 1 if left_val > right_val else 0
            elif ast_node.operator == ">=":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '>=' at line {ast_node.line}.")
                return 1 if left_val >= right_val else 0
        elif isinstance(ast_node,parser.CallExpr):
            # Function call：先求出所有實參，再分流到內建函式或使用者自訂函式。
            # 內建函式透過 c_builtins 呼叫；使用者函式交給 call_user_function() 建立 scope/stack frame。
            if not isinstance(ast_node.fn, parser.Identifier):
                raise Exception(f"Runtime error: Function name must be an identifier at line {ast_node.line}.")
            # print("func call:", ast_node.fn, "args:", ast_node.args)
            function_name = ast_node.fn.name
            args = []
            return_value = None
            for arg in ast_node.args:
                # Function call 的實參一律先套用 array-to-pointer decay：
                #   "abc" -> char*、char buf[] -> char*、int arr[] -> int*。
                # 這樣 built-in 與 user-defined function 都共用同一套參數轉換規則。
                args.append(self.decay_array_value(self.evaluate(arg)))
            if function_name in BUILTIN_SIGNATURES:
                return_value = self.call_builtin_function(function_name, args, ast_node.line)
            else:
                return_value = self.call_user_function(function_name, args, ast_node.line)
            return return_value
        elif isinstance(ast_node, parser.FunctionDef):
            # 函式定義只註冊到函式表，不會立即執行 body。
            params = []
            for param in ast_node.params:
                # 函式表保留原始參數宣告型態，讓 FUNCS 可顯示 int a[] 而不是 int* a。
                # 實際呼叫時再由 effective_param_type() 將陣列參數退化成 pointer。
                params.append(symtable.ParamSymbol(param.name, param.param_type, param.is_array))
            self.symtable.define_function(ast_node.name, ast_node.return_type, params, ast_node.body, ast_node.line)
            return None
        elif isinstance(ast_node, parser.VarDecl):
            if ast_node.is_array:
                # 陣列目前只支援 int/char 元素；指標陣列先保守拒絕，避免 memory.write() 無法處理。
                if ast_node.var_type not in ("int", "char"):
                    raise Exception(f"Runtime error: Array element type {ast_node.var_type} is not supported for variable '{ast_node.name}' at line {ast_node.line}.")
                if ast_node.array_size is None or ast_node.array_size <= 0:
                    raise Exception(f"Runtime error: Array '{ast_node.name}' length must be greater than 0 at line {ast_node.line}.")

                element_size = symtable.sizeof_type(ast_node.var_type)
                total_size = ast_node.array_size * element_size
                # 先求值並檢查初始化內容，避免初始化失敗後仍留下已註冊的陣列變數。
                init_values = None
                string_value = None

                if isinstance(ast_node.init_expr, parser.InitList):
                    init_values = []
                    for index, value_expr in enumerate(ast_node.init_expr.values):
                        value = self.evaluate(value_expr)
                        if not isinstance(value, int):
                            raise Exception(f"Runtime error: Cannot initialize array '{ast_node.name}' element {index} with value of type {type_mapping[type(value).__name__]} at line {ast_node.line}.")
                        init_values.append(value)
                elif isinstance(ast_node.init_expr, parser.String):
                    if ast_node.var_type != "char":
                        raise Exception(f"Runtime error: String initializer is only valid for char array '{ast_node.name}' at line {ast_node.line}.")
                    string_value = ast_node.init_expr.value
                elif ast_node.init_expr is not None:
                    raise Exception(f"Runtime error: Unsupported initializer for array '{ast_node.name}' at line {ast_node.line}.")

                # 初始化資料確認合法後，才真正配置記憶體並加入符號表。
                addr = self.alloc_for_current_scope(total_size)
                self.symtable.define_array(ast_node.name, ast_node.var_type, addr, ast_node.array_size, ast_node.line)

                if init_values is not None:
                    for index, value in enumerate(init_values):
                        self.memory.array_write(addr, index, ast_node.var_type, value)
                elif string_value is not None:
                    for index, ch in enumerate(string_value):
                        self.memory.array_write(addr, index, "char", ord(ch))
                    if len(string_value) < ast_node.array_size:
                        self.memory.array_write(addr, len(string_value), "char", 0)

                return None # 陣列宣告敘述不產生數值回傳

            # 1. 計算所需記憶體大小並配置空間
            size = 0
            if ast_node.var_type == "int":
                size = 4
            elif ast_node.var_type == "char":
                size = 1
            elif ast_node.var_type == "char*":
                size = 4 # 在 32 位元環境中，指標大小為 4 bytes
            elif ast_node.var_type == "int*":
                size = 4 # 在 32 位元環境中，指標大小為 4 bytes
            else:
                raise Exception(f"Runtime error: Unsupported variable type {ast_node.var_type} for variable '{ast_node.name}' at line {ast_node.line}.")
            init_val = None
            if ast_node.init_expr is not None:
                # 宣告的右側可能引用未定義變數或型別不合；先驗證，成功後才建立新變數。
                init_val = self.evaluate(ast_node.init_expr)
                if ast_node.var_type in ("int*", "char*"):
                    init_val = self.decay_array_value(init_val)
                valid_init = (
                    (ast_node.var_type == "int" and isinstance(init_val, int))
                    or (ast_node.var_type == "char" and isinstance(init_val, int))
                    or (ast_node.var_type == "int*" and isinstance(init_val, int_ptr))
                    or (ast_node.var_type == "char*" and isinstance(init_val, char_ptr))
                )
                if not valid_init:
                    if ast_node.var_type in ("int*", "char*") and isinstance(init_val, int):
                        raise Exception(f"Runtime error: Cannot initialize pointer '{ast_node.name}' with integer value {init_val}; omit initializer for NULL pointer at line {ast_node.line}.")
                    raise Exception(f"Runtime error: Cannot initialize variable '{ast_node.name}' of type {ast_node.var_type} with value of type {type_mapping[type(init_val).__name__]} at line {ast_node.line}.")

            addr = self.alloc_for_current_scope(size)

            # 初始值已經驗證成功後才註冊變數，避免錯誤宣告污染符號表。
            self.symtable.define_var(ast_node.name, ast_node.var_type, addr, ast_node.line)

            if init_val is not None:
                if ast_node.var_type == "int":
                    self.memory.set_int(addr, init_val)
                elif ast_node.var_type == "char":
                    self.memory.set_char(addr, init_val)
                elif ast_node.var_type == "int*":
                    self.memory.set_ptr(addr, init_val.addr)
                elif ast_node.var_type == "char*":
                    self.memory.set_ptr(addr, init_val.addr)
            return None # 宣告敘述不產生數值回傳
        elif isinstance(ast_node, parser.Identifier):
            # 變數取值：先查符號表拿位址，再從記憶體讀值
            var_info = self.symtable.lookup_var(ast_node.name)
            if var_info.is_array:
                # 陣列名稱在 expression 中先保留成 array 物件，函式呼叫時再 decay 成 pointer。
                return array(var_info.addr, var_info.array_length, var_info.var_type)
            if var_info.var_type == 'int':
                return self.memory.get_int(var_info.addr)
            elif var_info.var_type == 'char':
                return self.memory.get_char(var_info.addr)
            elif var_info.var_type == 'int*':
                target_addr = self.memory.get_ptr(var_info.addr) # 先讀出指標變數本身的值（也就是它指向的地址）
                return int_ptr(target_addr)
            elif var_info.var_type == 'char*': 
                target_addr = self.memory.get_ptr(var_info.addr) # 先讀出指標變數本身的值（也就是它指向的地址）
                return char_ptr(target_addr)
            else:
                raise Exception(f"Runtime error: Unsupported variable type {var_info.var_type} for variable '{ast_node.name}' at line {ast_node.line}.")
        elif isinstance(ast_node, parser.IndexExpr):
            # C 中 p[i] 等同 *(p + i)，因此 base 可以是陣列，也可以是 int*/char* 指標 expression。
            base_val = self.evaluate(ast_node.base)
            index = self.evaluate(ast_node.index)
            if not isinstance(index, int):
                raise Exception(f"Runtime error: Array index must be int at line {ast_node.line}.")

            if isinstance(base_val, array):
                return self.memory.array_read(base_val.addr, index, base_val.elem_type)
            if isinstance(base_val, int_ptr):
                target_addr = self.memory.ptr_add(base_val.addr, index, "int")
                self.memory.check_ptr(target_addr, 4)
                return self.memory.get_int(target_addr)
            if isinstance(base_val, char_ptr):
                target_addr = self.memory.ptr_add(base_val.addr, index, "char")
                self.memory.check_ptr(target_addr, 1)
                return self.memory.get_char(target_addr)
            raise Exception(f"Runtime error: Cannot apply index operator to {type_mapping[type(base_val).__name__]} at line {ast_node.line}.")
        elif isinstance(ast_node, parser.AssignmentExpr):
            # 指定運算統一透過左值解析取得寫入地址，因此支援 x、*p、arr[i]、p[i]。
            target_addr, target_type = self.resolve_lvalue(ast_node.left)
            right_val = self.evaluate(ast_node.right)
            if target_type in ("int*", "char*"):
                right_val = self.decay_array_value(right_val)
            # 取得舊值 (用以支援 +=, -= 等複合運算)
            old_val = None
            if ast_node.operator != "=":
                old_val = self.read_lvalue(target_addr, target_type)
            # 算出新值
            if ast_node.operator == "=": 
                if target_type == 'int*' or target_type == 'char*':
                    if isinstance(right_val, int):
                        raise Exception(f"Runtime error: Cannot assign integer value {right_val} to {target_type} at line {ast_node.line}.")
                new_val = right_val
            elif ast_node.operator == "+=": 
                if isinstance(old_val, int) and isinstance(right_val, int):
                    new_val = old_val + right_val
                # p += n 等同 p = p + n，位移與邊界檢查交給 ptr_add()。
                elif isinstance(old_val, int_ptr) and isinstance(right_val, int):
                    new_val = int_ptr(self.memory.ptr_add(old_val.addr, right_val, "int"))
                elif isinstance(old_val, char_ptr) and isinstance(right_val, int):
                    new_val = char_ptr(self.memory.ptr_add(old_val.addr, right_val, "char"))
                else:
                    raise Exception(f"Runtime error: Cannot apply operator '+=' to {type_mapping[type(old_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
            elif ast_node.operator == "-=": 
                if isinstance(old_val, int) and isinstance(right_val, int):
                    new_val = old_val - right_val
                # p -= n 使用負 offset，仍保留 int*/char* 各自的 stride。
                elif isinstance(old_val, int_ptr) and isinstance(right_val, int):
                    new_val = int_ptr(self.memory.ptr_add(old_val.addr, -right_val, "int"))
                elif isinstance(old_val, char_ptr) and isinstance(right_val, int):
                    new_val = char_ptr(self.memory.ptr_add(old_val.addr, -right_val, "char"))
                else:
                    raise Exception(f"Runtime error: Cannot apply operator '-=' to {type_mapping[type(old_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
            elif ast_node.operator == "*=":
                if not isinstance(old_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '*=' to {type_mapping[type(old_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.") 
                new_val = old_val * right_val
            elif ast_node.operator == "/=":
                if not isinstance(old_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '/=' to {type_mapping[type(old_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                if right_val == 0:
                    raise Exception(f"Runtime error: Division by zero at line {ast_node.line}.")
                new_val = c_div(old_val, right_val)
            elif ast_node.operator == "%=": 
                if not isinstance(old_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '%=' to {type_mapping[type(old_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                if right_val == 0:
                    raise Exception(f"Runtime error: Modulo by zero at line {ast_node.line}.")
                new_val = c_mod(old_val, right_val)
            
            # 寫入記憶體
            self.write_lvalue(target_addr, target_type, new_val, ast_node.line)
            return new_val

        elif isinstance(ast_node, parser.ExpressionStmt):
            # 只有這裡代表 expression 被當成完整語句執行；內部 expression 節點不應各自輸出 TRACE。
            return self.evaluate(ast_node.expr)
        
        elif isinstance(ast_node, parser.EmptyStmt):
            return None
        elif isinstance(ast_node, parser.IfStmt):
            # if/else 依條件值決定只執行其中一個分支。
            if self.evaluate(ast_node.condition) != 0:
                self.evaluate(ast_node.then_branch)
            elif ast_node.else_branch is not None:
                self.evaluate(ast_node.else_branch)
            return None
        elif isinstance(ast_node, parser.WhileStmt):
            # while 只要條件成立就持續回圈執行 body。
            while self.evaluate(ast_node.condition) != 0:
                try:
                    self.evaluate(ast_node.body)
                except ContinueSignal:
                    # continue 跳過本輪剩餘敘述，回到 while 條件檢查。
                    continue
                except BreakSignal:
                    # break 結束最近一層 while 迴圈。
                    break
            return None
        elif isinstance(ast_node, parser.DoWhileStmt):
            # do-while 的 continue 仍需先檢查條件，再決定是否進入下一輪。
            while True:
                try:
                    self.evaluate(ast_node.body)
                except ContinueSignal:
                    # do-while 的 continue 不直接進下一輪，而是先落到下方條件檢查。
                    pass
                except BreakSignal:
                    # break 結束最近一層 do-while 迴圈。
                    break
                if self.evaluate(ast_node.condition) == 0:
                    break
            return None
        elif isinstance(ast_node, parser.ForStmt):
            # for 的 init 宣告（例如 for (int i = 0; ...)）需要活到 condition、body、update
            # 都執行完，因此 loop scope 必須包住整個 for，而不是只包 body block。
            frame_entry_top = self.memory.stack_top
            self.symtable.push_scope()
            try:
                if ast_node.init is not None:
                    self.evaluate(ast_node.init)
                while True:
                    if ast_node.condition is not None and self.evaluate(ast_node.condition) == 0:
                        break
                    try:
                        self.evaluate(ast_node.body)
                    except ContinueSignal:
                        pass
                    except BreakSignal:
                        break
                    if ast_node.update is not None:
                        self.evaluate(ast_node.update)
            finally:
                self.symtable.pop_scope()
                self.memory.free_stack_frame(frame_entry_top)
            return None
        elif isinstance(ast_node, parser.SwitchStmt):
            switch_value = self.evaluate(ast_node.expr)
            if not isinstance(switch_value, int):
                raise Exception(f"Runtime error: switch expression must be int at line {ast_node.line}.")

            # switch 的 case/default 共享同一個 switch block scope；case 內宣告的變數
            # 離開 switch 後必須消失，但 fall-through 期間仍維持可見。
            frame_entry_top = self.memory.stack_top
            self.symtable.push_scope()
            try:
                # C-like switch：先找到第一個符合的 case；沒有符合時才跳到 default。
                # 從命中的 clause 開始一路執行後續 clause，直到 break 或 switch 結尾，藉此保留 fall-through 行為。
                start_index = None
                default_index = None
                for index, clause in enumerate(ast_node.clauses):
                    if clause.is_default:
                        # parser 已保證 default 最多一個；這裡只記錄無 case 命中時的備援入口。
                        default_index = index
                    elif clause.value == switch_value and start_index is None:
                        start_index = index

                if start_index is None:
                    start_index = default_index
                if start_index is None:
                    return None

                try:
                    # 只攔截 break：continue 必須穿透到外層 loop，return 必須穿透到外層函式呼叫。
                    for clause in ast_node.clauses[start_index:]:
                        for stmt in clause.statements:
                            self.evaluate(stmt)
                except BreakSignal:
                    # break 結束最近一層 switch；continue/return 不在這裡攔截，交給外層 loop/function。
                    return None
            finally:
                self.symtable.pop_scope()
                self.memory.free_stack_frame(frame_entry_top)
            return None
        elif isinstance(ast_node, parser.BreakStmt):
            # 交給外層最近的迴圈或 switch 處理。
            raise BreakSignal()
        elif isinstance(ast_node, parser.ContinueStmt):
            # 交給外層最近的迴圈處理。
            raise ContinueSignal()
        elif isinstance(ast_node, parser.ReturnStmt):
            # return 不在這裡直接結束 evaluate；改用 ReturnSignal 交給最近的 CallExpr 接住。
            value = None if ast_node.expr is None else self.evaluate(ast_node.expr)
            raise ReturnSignal(value, ast_node.line)
        elif isinstance(ast_node, parser.Block):
            # 一般 { ... } block 會建立自己的區域 scope。
            # return / break / continue 以 exception signal 傳出時，finally 仍會清理
            # 這個 block 配置的區域變數，避免污染外層 scope 或後續 REPL 狀態。
            frame_entry_top = self.memory.stack_top
            self.symtable.push_scope()
            try:
                for stmt in ast_node.statements:
                    self.evaluate(stmt)
            finally:
                self.symtable.pop_scope()
                self.memory.free_stack_frame(frame_entry_top)
            return None
        else:
            raise Exception(f"Runtime error: Unsupported AST node type {type(ast_node).__name__} at line {ast_node.line}.")
