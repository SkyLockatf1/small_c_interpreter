import importlib.util
import os
import inspect
import parser
import memory
import symtable as symtable

# 將 Python 執行時的型別名稱轉成錯誤訊息中較接近 C 語言的型別名稱。
type_mapping = {
    'str': 'char*',
    'int': 'int'
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
str_funcs = ["memset","strlen","strcmp","strcpy","strcat","printf","puts"]

class Interpreter:
    def __init__(self):
        # 保存目前執行環境的虛擬記憶體與符號表，後續求值時會用來查變數、地址與函式。
        self.memory:memory = memory.VirtualMemory()
        self.symtable:symtable = symtable.symtable()
    def evaluate(self, ast_node):
        # 根據 AST 節點型別遞迴求值，回傳此節點在目前執行環境中的值。
        if isinstance(ast_node, parser.Number):
            return ast_node.value
        elif isinstance(ast_node, parser.Char):
            return ast_node.value 
        elif isinstance(ast_node, parser.String):
            return self.memory.set_string(ast_node.value) #放進記憶體並回傳地址
        elif isinstance(ast_node, parser.Pointer):
            pass # 這裡要實作指標取值邏輯，類似 C 語言的 *ptr
        elif isinstance(ast_node, parser.UnaryExpr):
            # 一元運算會先求出 operand 的值，再依照運算子做型別檢查與計算。
            val = self.evaluate(ast_node.operand)
            if ast_node.operator == "-":
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '-' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return -val
            elif ast_node.operator == "!":
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '+' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return int(not val)
            elif ast_node.operator == "~":
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '~' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return ~val
            elif ast_node.operator == "++" and ast_node.postfix == False:
                # 目前只處理前置 ++ 的回傳值，尚未把結果寫回變數本身。
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '++' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return val + 1
            elif ast_node.operator == "--" and ast_node.postfix == False:
                # 目前只處理前置 -- 的回傳值，尚未把結果寫回變數本身。
                if not isinstance(val, (int)):
                    raise Exception(f"Runtime error: Cannot apply unary '--' to {type_mapping[type(val).__name__]} at line {ast_node.line}.")
                return val - 1
                
                
        elif isinstance(ast_node, parser.BinaryExpr):
            # 二元運算會先求左右子表達式，再依照運算子檢查型別並產生結果。
            left_val = self.evaluate(ast_node.left)
            right_val = self.evaluate(ast_node.right)
            if ast_node.operator == "+":
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
                return left_val // right_val
            elif ast_node.operator == "%":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '%' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return left_val % right_val
            elif ast_node.operator == "&":
                if type(left_val) != type(right_val):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '&' at line {ast_node.line}.")
                return left_val & right_val
            elif ast_node.operator == "|":
                if type(left_val) != type(right_val):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '|' at line {ast_node.line}.")
                return left_val | right_val
            elif ast_node.operator == "^":
                if type(left_val) != type(right_val):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '^' at line {ast_node.line}.")
                return left_val ^ right_val
            elif ast_node.operator == "<<":
                if type(left_val) != type(right_val):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '<<' at line {ast_node.line}.")
                return left_val << right_val
            elif ast_node.operator == ">>":
                if type(left_val) != type(right_val):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '>>' at line {ast_node.line}.")
                return left_val >> right_val
            elif ast_node.operator == "==":
                if type(left_val) != type(right_val):
                    raise Exception(f"Runtime error: Cannot compare {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} with '==' at line {ast_node.line}.")
                return 1 if left_val == right_val else 0
            elif ast_node.operator == "!=":
                if type(left_val) != type(right_val):
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
            elif ast_node.operator == "&&":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '&&' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return 1 if left_val and right_val else 0
            elif ast_node.operator == "||":
                if not isinstance(left_val, (int)) or not isinstance(right_val, (int)):
                    raise Exception(f"Runtime error: Cannot apply operator '||' to {type_mapping[type(left_val).__name__]} and {type_mapping[type(right_val).__name__]} at line {ast_node.line}.")
                return 1 if left_val or right_val else 0
        elif isinstance(ast_node,parser.CallExpr):
            # 函式呼叫會先求出所有參數，再分流到內建函式或使用者自訂函式。
            print("func call:", ast_node.fn, "args:", ast_node.args)
            function_name = ast_node.fn.name
            args = []
            for arg in ast_node.args:
                args.append(self.evaluate(arg))
            if function_name in builtins_funcs:
                if function_name in str_funcs:
                    getattr(c_builtins,function_name)(self.memory,*args)
                else:
                    getattr(c_builtins,function_name)(*args)
            else:
                pass # 這裡要實作呼叫 user-defined 函式的邏輯，從符號表查函式定義，建立新的執行環境，執行函式體等
        elif isinstance(ast_node, parser.VarDecl):
            # 1. 計算所需記憶體大小並配置空間
            size = 4 if ast_node.var_type == "int" else 1
            addr = self.memory.alloc_global(size)
            
            # 2. 註冊進符號表
            self.symtable.define(ast_node.name, ast_node.var_type, addr)
            
            # 3. 如果有給初始值，算出來並寫入記憶體
            if ast_node.init_expr:
                val = self.evaluate(ast_node.init_expr)
                if ast_node.var_type == "int":
                    self.memory.set_int(addr, val)
                elif ast_node.var_type == "char":
                    self.memory.set_char(addr, val)
            return None # 宣告敘述不產生數值回傳
        elif isinstance(ast_node, parser.Identifier):
            # 變數取值：先查符號表拿位址，再從記憶體讀值
            var_info = self.symtable.lookup(ast_node.name)
            if var_info['type'] == 'int':
                return self.memory.get_int(var_info['addr'])
            elif var_info['type'] == 'char':
                return self.memory.get_char(var_info['addr'])
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
            # (你可以依樣畫葫蘆補齊 *=, /=, %=)
            
            # 寫入記憶體
            if var_info['type'] == 'int':
                self.memory.set_int(var_info['addr'], new_val)
            elif var_info['type'] == 'char':
                self.memory.set_char(var_info['addr'], new_val)
                
            return new_val
            
