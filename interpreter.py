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

# break / continue 可能出現在巢狀 block 或 if 裡，
# 用內部 signal 往外傳遞，直到最近的迴圈節點接住。
class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

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
        self._rng = random.Random(1)
        self.randseed = 1

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

    def call_user_function(self, function_name: str, arg_values: list, line: int):
        """呼叫使用者定義函式：建立參數 scope、執行 body，並處理 return 值。"""
        # 從函式表取得先前由 FunctionDef 註冊的簽名與 body。
        func = self.symtable.lookup_function(function_name)
        if len(arg_values) != len(func.params):
            raise Exception(f"Runtime error: Function '{function_name}' expects {len(func.params)} arguments, got {len(arg_values)} at line {line}.")

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
                # 執行函式 body；return 會以 ReturnSignal 方式跳出巢狀 block / if / loop。
                self.evaluate(func.body)
            except ReturnSignal as signal:
                if func.return_type == "void":
                    if signal.value is not None:
                        raise Exception(f"Runtime error: Void function '{function_name}' should not return a value at line {signal.line}.")
                    return None
                if signal.value is None:
                    raise Exception(f"Runtime error: Function '{function_name}' must return {func.return_type} at line {signal.line}.")
                # 非 void 函式要檢查 return value 是否符合宣告回傳型別。
                return self.validate_value_for_type(signal.value, func.return_type, signal.line, f"return from '{function_name}'")

            if func.return_type != "void":
                raise Exception(f"Runtime error: Function '{function_name}' ended without returning {func.return_type} at line {line}.")
            return None
        finally:
            # 無論正常 return 或執行期錯誤，都必須復原 scope 與 stack frame，避免污染後續 REPL 狀態。
            self.symtable.pop_scope()
            self.memory.free_stack_frame(frame_entry_top)

    def evaluate(self, ast_node):
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
            print("func call:", ast_node.fn, "args:", ast_node.args)
            function_name = ast_node.fn.name
            args = []
            return_value = None
            for arg in ast_node.args:
                # Function call 的實參一律先套用 array-to-pointer decay：
                #   "abc" -> char*、char buf[] -> char*、int arr[] -> int*。
                # 這樣 built-in 與 user-defined function 都共用同一套參數轉換規則。
                args.append(self.decay_array_value(self.evaluate(arg)))
            if function_name == "rand":
                if len(args) != 0:
                    raise Exception(f"Runtime error: rand expects 0 arguments, got {len(args)} at line {ast_node.line}.")
                return c_builtins.rand(self._rng)
            if function_name == "srand":
                if len(args) != 1:
                    raise Exception(f"Runtime error: srand expects 1 argument, got {len(args)} at line {ast_node.line}.")
                if not isinstance(args[0], int):
                    got_type = type_mapping.get(type(args[0]).__name__, type(args[0]).__name__)
                    raise Exception(f"Runtime error: srand expects int, got {got_type} at line {ast_node.line}.")
                self.randseed = args[0]
                return c_builtins.srand(self._rng, args[0])
            if function_name in builtins_funcs:
                if function_name in str_funcs:
                    return_value = getattr(c_builtins,function_name)(self.memory,*args)
                else:
                    return_value = getattr(c_builtins,function_name)(*args)
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
        elif isinstance(ast_node, parser.ReturnStmt):
            # return 不在這裡直接結束 evaluate；改用 ReturnSignal 交給最近的 CallExpr 接住。
            value = None if ast_node.expr is None else self.evaluate(ast_node.expr)
            raise ReturnSignal(value, ast_node.line)
        elif isinstance(ast_node, parser.Block):
            # 區塊按順序執行其中每一個語句。
            for stmt in ast_node.statements:
                self.evaluate(stmt)
            return None
        else:
            raise Exception(f"Runtime error: Unsupported AST node type {type(ast_node).__name__} at line {ast_node.line}.")
