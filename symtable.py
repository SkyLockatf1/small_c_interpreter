from typing import Iterator


# ── 型別輔助函式 ──────────────────────────────────────────────────────────────
# 集中處理型別字串的判斷與大小計算，避免 interpreter 到處手寫相同邏輯。

def is_pointer_type(var_type: str) -> bool:
    """判斷型別字串是否為指標（以 * 結尾）。"""
    return var_type.endswith("*")


def pointee_type(var_type: str) -> str:
    """回傳指標型別的目標型別，例如 'int*' -> 'int'。"""
    if not is_pointer_type(var_type):
        raise Exception(f"Runtime error: Type '{var_type}' is not a pointer type.")
    return var_type[:-1]


def sizeof_type(var_type: str) -> int:
    """回傳基本型別的位元組大小，指標統一視為 4 bytes（32 位元環境）。"""
    if var_type == "int":
        return 4
    if var_type == "char":
        return 1
    if var_type in ("int*", "char*"):
        return 4
    raise Exception(f"Runtime error: Unsupported type '{var_type}'.")


# ── 資料模型 ──────────────────────────────────────────────────────────────────
# 明確描述符號表內每種符號的欄位，取代舊有的裸 dict。

class VarSymbol:
    """代表一個變數、陣列或指標符號。"""

    def __init__(self, name, var_type, addr, size, scope_level,
                 is_array=False, array_length=None, element_size=None, line=None):
        self.name = name
        self.var_type = var_type        # "int" / "char" / "int*" / "char*"
        self.addr = addr                # 在虛擬記憶體中的起始位址
        self.size = size                # 佔用的位元組總數
        self.scope_level = scope_level  # 宣告所在的 scope 深度，0 為全域
        self.is_array = is_array
        self.array_length = array_length    # 僅陣列有效
        self.element_size = element_size    # 僅陣列有效，單一元素的位元組數
        self.line = line                    # 宣告所在的原始碼行號，用於錯誤訊息

    def __repr__(self):
        return (f"VarSymbol(name={self.name!r}, var_type={self.var_type!r}, "
                f"addr={self.addr}, size={self.size}, scope_level={self.scope_level}, "
                f"is_array={self.is_array}, array_length={self.array_length}, "
                f"element_size={self.element_size}, line={self.line})")


class ParamSymbol:
    """代表函式的一個參數，僅記錄型別資訊，不佔記憶體位址。"""

    def __init__(self, name, var_type, is_array=False):
        self.name = name
        self.var_type = var_type    # "int" / "char" / "int*" / "char*"
        self.is_array = is_array    # 參數宣告為陣列時（如 int a[]）

    def __repr__(self):
        return f"ParamSymbol(name={self.name!r}, var_type={self.var_type!r}, is_array={self.is_array})"


class FunctionSymbol:
    """代表一個函式定義，包含簽名與 AST body。"""

    def __init__(self, name, return_type, params, body, line=None):
        self.name = name
        self.return_type = return_type  # "int" / "char" / "void" / "int*" / "char*"
        self.params = params
        self.body = body                # 函式 body 的 AST 節點
        self.line = line

    def __repr__(self):
        return (f"FunctionSymbol(name={self.name!r}, return_type={self.return_type!r}, "
                f"params={self.params!r}, line={self.line})")


# ── 符號表 ────────────────────────────────────────────────────────────────────

class symtable:
    def __init__(self):
        # scopes 是 scope stack，scopes[0] 為全域 scope。
        # 每個 scope 是一個 dict，從變數名稱映射到 VarSymbol。
        self.scopes: list[dict[str, VarSymbol]] = [{}]
        # functions 是獨立的函式命名空間，與變數 namespace 分開，
        # 因此變數與函式可以同名（接近 C 語言行為）。
        self.functions: dict[str, FunctionSymbol] = {}

    # ── 變數 API ──────────────────────────────────────────────────────────────

    def define_var(self, name: str, var_type: str, addr: int, line: int | None = None) -> VarSymbol:
        """在目前 scope 宣告一個 scalar 或指標變數。同 scope 內重複宣告視為錯誤。"""
        current = self.scopes[-1]
        if name in current:
            raise Exception(f"Runtime error: Variable '{name}' is already defined.")
        size = sizeof_type(var_type)
        sym = VarSymbol(
            name=name,
            var_type=var_type,
            addr=addr,
            size=size,
            scope_level=len(self.scopes) - 1,
            line=line,
        )
        current[name] = sym
        return sym

    def define_array(self, name: str, var_type: str, addr: int, length: int, line: int | None = None) -> VarSymbol:
        """在目前 scope 宣告一個陣列變數，自動計算總大小並設定陣列 metadata。"""
        current = self.scopes[-1]
        if name in current:
            raise Exception(f"Runtime error: Variable '{name}' is already defined.")
        if length <= 0:
            raise Exception(f"Runtime error: Array '{name}' length must be greater than 0.")
        element_size = sizeof_type(var_type)
        sym = VarSymbol(
            name=name,
            var_type=var_type,
            addr=addr,
            size=length * element_size,
            scope_level=len(self.scopes) - 1,
            is_array=True,
            array_length=length,
            element_size=element_size,
            line=line,
        )
        current[name] = sym
        return sym

    def lookup_var(self, name: str) -> VarSymbol:
        """從最近的 scope 往全域 scope 搜尋變數，支援內層變數遮蔽外層。"""
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise Exception(f"Runtime error: Undefined variable '{name}'.")

    # ── 函式 API ──────────────────────────────────────────────────────────────

    def define_function(self, name: str, return_type: str, params: list[ParamSymbol], body: object, line: int | None = None) -> FunctionSymbol:
        """在全域函式表中註冊一個使用者定義函式。不允許重複定義同名函式。"""
        if name in self.functions:
            raise Exception(f"Runtime error: Function '{name}' is already defined.")
        sym = FunctionSymbol(
            name=name,
            return_type=return_type,
            params=params,
            body=body,
            line=line,
        )
        self.functions[name] = sym
        return sym

    def lookup_function(self, name: str) -> FunctionSymbol:
        """在全域函式表中查找函式，找不到時回報錯誤。"""
        if name not in self.functions:
            raise Exception(f"Runtime error: Undefined function '{name}'.")
        return self.functions[name]

    # ── Scope 管理 ────────────────────────────────────────────────────────────

    def push_scope(self):
        """進入新的區塊 scope，例如函式呼叫或複合語句開始時。"""
        self.scopes.append({})

    def pop_scope(self):
        """離開目前 scope，全域 scope 不允許被移除。"""
        if len(self.scopes) <= 1:
            raise Exception("Runtime error: Cannot pop global scope.")
        self.scopes.pop()

    def current_scope_level(self) -> int:
        """回傳目前 scope 的深度，0 為全域。"""
        return len(self.scopes) - 1

    def reset(self):
        """清空所有變數 scope 與函式表，供 NEW 指令重置執行環境時使用。"""
        self.scopes = [{}]
        self.functions = {}

    # ── 迭代器 ────────────────────────────────────────────────────────────────

    def iter_vars(self) -> Iterator[VarSymbol]:
        """產出全域變數符號，供 VARS 指令顯示使用。"""
        yield from self.scopes[0].values()

    def iter_functions(self) -> Iterator[FunctionSymbol]:
        """產出函式表中所有使用者定義的函式符號。"""
        yield from self.functions.values()

    # ── 向下相容 API ──────────────────────────────────────────────────────────
    # 過渡期保留舊介面，讓 interpreter.py 與 main.py 不需要同步修改。
    # 等上層全部改用新 API 後再移除。

    def define(self, name: str, var_type: str, addr: int):
        """舊 API：宣告 scalar 或指標變數，size 由 sizeof_type 自動推算。"""
        self.define_var(name, var_type, addr)

    def lookup(self, name: str) -> dict:
        """舊 API：查找變數，回傳與舊格式相同的 {'type': ..., 'addr': ...}。"""
        sym = self.lookup_var(name)
        return {"type": sym.var_type, "addr": sym.addr}

    @property
    def table(self) -> dict:
        """舊 API：回傳全域變數的快照，供 VARS 指令沿用舊格式顯示。"""
        result = {}
        for name, sym in self.scopes[0].items():
            result[name] = {"type": sym.var_type, "addr": sym.addr}
        return result
