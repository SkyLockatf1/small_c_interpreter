import importlib.util
import os
import inspect
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
    if obj.__module__ == c_builtins.__name__:
        builtins_funcs.append(name)

# 字串相關函式需要讀寫虛擬記憶體，因此呼叫時會額外傳入 memory 物件。
str_funcs = ["memset","strlen","strcmp","strcpy","strcat","printf","puts","scanf"]

# break / continue 可能出現在巢狀 block 或 if 裡，
# 用內部 signal 往外傳遞，直到最近的迴圈節點接住。
class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

class Interpreter:
    """執行 AST 的狀態容器。"""

    def __init__(self):
        # 保存目前執行環境的虛擬記憶體與符號表，後續求值時會用來查變數、地址與函式。
        self.memory: memory.VirtualMemory = memory.VirtualMemory()
        self.symtable: symtable.symtable = symtable.symtable()
        self.randseed = None # 之後實作 rand() 時會用到

    def evaluate(self, ast_node) -> object:
        # 根據 AST 節點型別遞迴求值，回傳此節點在目前執行環境中的值。
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
            if ast_node.operator == "-":
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
                if not isinstance(ast_node.operand, parser.Identifier):
                    raise Exception(f"Runtime error: Cannot apply unary '&' to non-variable at line {ast_node.line}.")
                pass# 這裡要實作取地址邏輯，類似 C 語言的 &var，從符號表查出變數的位址並回傳
            elif ast_node.operator == "++" and ast_node.postfix == False:
                if not isinstance(ast_node.operand, parser.Identifier):
                    raise Exception(f"Runtime error: Cannot apply unary '++' to non-variable at line {ast_node.line}.")
                var_info = self.symtable.lookup(ast_node.operand.name)
                old_val=0
                if var_info['type'] == 'int':
                    old_val = self.memory.get_int(var_info['addr'])
                    self.memory.set_int(var_info['addr'], old_val + 1)
                elif var_info['type'] == 'char':
                    old_val = self.memory.get_char(var_info['addr'])
                    self.memory.set_char(var_info['addr'], old_val + 1)
                else:
                    raise Exception(f"Runtime error: Unsupported variable type {var_info['type']} for variable '{ast_node.operand.name}' at line {ast_node.line}.")
                return old_val + 1
            elif ast_node.operator == "--" and ast_node.postfix == False:
                if not isinstance(ast_node.operand, parser.Identifier):
                    raise Exception(f"Runtime error: Cannot apply unary '--' to non-variable at line {ast_node.line}.")
                var_info = self.symtable.lookup(ast_node.operand.name)
                old_val=0
                if var_info['type'] == 'int':
                    old_val = self.memory.get_int(var_info['addr'])
                    self.memory.set_int(var_info['addr'], old_val - 1)
                elif var_info['type'] == 'char':
                    old_val = self.memory.get_char(var_info['addr'])
                    self.memory.set_char(var_info['addr'], old_val - 1)
                else:
                    raise Exception(f"Runtime error: Unsupported variable type {var_info['type']} for variable '{ast_node.operand.name}' at line {ast_node.line}.")
                return old_val - 1
                
                
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
            if ast_node.operator == "+":
                # 這裡對每個運算子都檢查左右兩邊的值是否為 int（或 char 以 int 形式），確保類型正確才進行運算，否則丟出錯誤訊息。
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '+' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val + right_val
            elif ast_node.operator == "-":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '-' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val - right_val
            elif ast_node.operator == "*":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '*' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val * right_val
            elif ast_node.operator == "/":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '/' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                if right_val == 0:
                    raise Exception(f"Runtime error: Division by zero at line {ast_node.line}.")
                return left_val // right_val
            elif ast_node.operator == "%":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '%' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                if right_val == 0:
                    raise Exception(f"Runtime error: Modulo by zero at line {ast_node.line}.")
                return left_val % right_val
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
            # 函式呼叫會先求出所有參數，再分流到內建函式或使用者自訂函式。
            """目前只實作內建函式的呼叫邏輯，使用 Python 的 getattr 從 c_builtins 模組找到對應函式並呼叫。
            之後要實作 user-defined 函式的呼叫邏輯，從符號表查函式定義，建立新的執行環境，執行函式體等。
            缺少對參數類型與數量的檢查，以及對 return 值的處理，目前先假設內建函式都能正確被呼叫，且 user-defined 函式的呼叫邏輯尚未實作。"""
            if not isinstance(ast_node.fn, parser.Identifier):
                raise Exception(f"Runtime error: Function name must be an identifier at line {ast_node.line}.")
            print("func call:", ast_node.fn, "args:", ast_node.args)
            function_name = ast_node.fn.name
            args = []
            return_value = None
            for arg in ast_node.args:
                args.append(self.evaluate(arg))
                if isinstance(args[-1], array):
                    # 如果參數是字串常數，將其轉換成 char_ptr 傳給內建函式。
                    if args[-1].elem_type == 'char':
                        args[-1] = char_ptr(args[-1].addr, args[-1].length)
                    elif args[-1].elem_type == 'int':
                        args[-1] = int_ptr(args[-1].addr)
                    else:
                        raise Exception(f"Runtime error: Unsupported array element type {args[-1].elem_type} for argument at line {ast_node.line}.")
            if function_name in builtins_funcs:
                if function_name in str_funcs:
                    return_value = getattr(c_builtins,function_name)(self.memory,*args)
                else:
                    return_value = getattr(c_builtins,function_name)(*args)
            else:
                pass # 這裡要實作呼叫 user-defined 函式的邏輯，從符號表查函式定義，建立新的執行環境，執行函式體等
            return return_value
        elif isinstance(ast_node, parser.VarDecl):
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
            addr = self.memory.alloc_global(size)
            
            # 2. 註冊進符號表
            self.symtable.define(ast_node.name, ast_node.var_type, addr)
            
            # 3. 如果有給初始值，算出來並寫入記憶體
            if ast_node.init_expr:
                val = self.evaluate(ast_node.init_expr)
                if ast_node.var_type == "int" and isinstance(val, (int)):
                    self.memory.set_int(addr, val)
                elif ast_node.var_type == "char" and isinstance(val, (int)):
                    self.memory.set_char(addr, val)
                else:
                    raise Exception(f"Runtime error: Cannot initialize variable '{ast_node.name}' of type {ast_node.var_type} with value of type {type_mapping[type(val).__name__]} at line {ast_node.line}.")
            return None # 宣告敘述不產生數值回傳
        elif isinstance(ast_node, parser.Identifier):
            # 變數取值：先查符號表拿位址，再從記憶體讀值
            var_info = self.symtable.lookup(ast_node.name)
            if var_info['type'] == 'int':
                return self.memory.get_int(var_info['addr'])
            elif var_info['type'] == 'char':
                return self.memory.get_char(var_info['addr'])
            else:
                raise Exception(f"Runtime error: Unsupported variable type {var_info['type']} for variable '{ast_node.name}' at line {ast_node.line}.")
        elif isinstance(ast_node, parser.AssignmentExpr):
            # 指定運算：目前我們只處理左邊是單純變數名的情況
            if not isinstance(ast_node.left, parser.Identifier):
                raise Exception(f"Runtime error: Left side of assignment must be a variable at line {ast_node.line}")
            
            var_info = self.symtable.lookup(ast_node.left.name)
            right_val = self.evaluate(ast_node.right)
            
            # 取得舊值 (用以支援 +=, -= 等複合運算)
            old_val = 0
            if ast_node.operator != "=":
                if var_info['type'] == 'int': old_val = self.memory.get_int(var_info['addr'])
                elif var_info['type'] == 'char': old_val = self.memory.get_char(var_info['addr'])
            
            # 算出新值
            if ast_node.operator == "=": new_val = right_val
            elif ast_node.operator == "+=": new_val = old_val + right_val
            elif ast_node.operator == "-=": new_val = old_val - right_val
            elif ast_node.operator == "*=": new_val = old_val * right_val
            elif ast_node.operator == "/=":
                if right_val == 0:
                    raise Exception(f"Runtime error: Division by zero at line {ast_node.line}.")
                new_val = old_val // right_val
            elif ast_node.operator == "%=": 
                if right_val == 0:
                    raise Exception(f"Runtime error: Modulo by zero at line {ast_node.line}.")
                new_val = old_val % right_val
            
            # 寫入記憶體
            if var_info['type'] == 'int':
                self.memory.set_int(var_info['addr'], new_val)
            elif var_info['type'] == 'char':
                self.memory.set_char(var_info['addr'], new_val)
                
            return new_val
        
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
            return None
        elif isinstance(ast_node, parser.BreakStmt):
            # 交給外層最近的迴圈處理。
            raise BreakSignal()
        elif isinstance(ast_node, parser.ContinueStmt):
            # 交給外層最近的迴圈處理。
            raise ContinueSignal()
        elif isinstance(ast_node, parser.Block):
            # 區塊按順序執行其中每一個語句。
            for stmt in ast_node.statements:
                self.evaluate(stmt)
            return None
        else:
            raise Exception(f"Runtime error: Unsupported AST node type {type(ast_node).__name__} at line {ast_node.line}.")
