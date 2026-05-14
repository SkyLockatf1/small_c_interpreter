# symtable.py 重構計劃

## 目標

重構 `symtable.py`，讓符號表可以穩定支援 Small-C 的變數、陣列、指標與函式儲存，並為後續 `VARS`、`FUNCS`、函式呼叫、遞迴、array / pointer 操作打基礎。

本次設計以課程作業驗收為優先，不擴充成完整 C 編譯器。

## 已確認決策

- `#define` 常數不放進 `symtable.py`，維持由 lexer / preprocess 階段處理。
- 變數與函式可以同名，接近 C 語言的 namespace 行為。
- 支援偏 C 的 array decay to pointer，例如 `int* p = a;`。
- 同一個 scope 內不允許重複宣告同名變數。
- 同名函式不允許重複定義。
- 函式 namespace 與變數 namespace 分開管理。

## 目前問題

目前 `symtable.py` 只有單一 dict：

```python
name -> {'type': var_type, 'addr': addr}
```

限制如下：

- 無法區分 scalar、array、pointer、function。
- 無法記錄 array 長度、元素型別、總大小。
- pointer 目前只靠字串型別 `int*` / `char*`，但缺少集中 helper 處理 pointer 判斷、pointee type 與大小計算。
- 沒有 function table，`CallExpr` 目前只能處理 builtins。
- 沒有 scope stack，函式參數、區域變數與遞迴都無法穩定支援。
- `main.py` 的 `VARS` 直接讀取 `symtable.table`，之後需要改用公開 iterator。

## Namespace 設計

符號表分成兩個 namespace：

```python
self.scopes = [{}]      # 變數 / array / pointer
self.functions = {}     # 函式
```

查找規則：

- 一般 identifier expression 使用 `lookup_var()`。
- function call expression 使用 `lookup_function()`。
- 變數與函式可同名，彼此不衝突。
- 變數查找從最近 scope 往 global scope 搜尋。
- 函式先以全域函式表管理，後續若沒有特殊需求，不支援巢狀函式。

允許以下形式：

```c
int foo;
int foo() {
    return 1;
}
```

## 建議資料模型

使用 `dataclass` 讓資料結構明確。若 Python 版本不支援 `int | None`，可改用 `Optional[int]`。

```python
from dataclasses import dataclass


@dataclass
class VarSymbol:
    name: str
    var_type: str          # "int" / "char" / "int*" / "char*"
    addr: int
    size: int
    scope_level: int
    is_array: bool = False
    array_length: int | None = None
    element_size: int | None = None
    line: int | None = None


@dataclass
class ParamSymbol:
    name: str
    var_type: str          # "int" / "char" / "int*" / "char*"
    is_array: bool = False


@dataclass
class FunctionSymbol:
    name: str
    return_type: str       # "int" / "char" / "void" / "int*" / "char*"
    params: list[ParamSymbol]
    body: object
    line: int | None = None
    is_builtin: bool = False
```

## 型別字串規則

本專案可直接使用 raw string 表示型別，因為目前 Small-C 子集只需要：

```python
"int"
"char"
"int*"
"char*"
```

但不要讓 interpreter 到處重複手寫判斷。建議集中提供 helper：

```python
is_pointer_type("int*") -> True
is_pointer_type("int") -> False
pointee_type("int*") -> "int"
pointee_type("char*") -> "char"
sizeof_type("int") -> 4
sizeof_type("char") -> 1
sizeof_type("int*") -> 4
sizeof_type("char*") -> 4
```

範例 helper：

```python
def is_pointer_type(var_type):
    return var_type.endswith("*")


def pointee_type(var_type):
    if not is_pointer_type(var_type):
        raise Exception(f"Runtime error: Type '{var_type}' is not a pointer type.")
    return var_type[:-1]


def sizeof_type(var_type):
    if var_type == "int":
        return 4
    if var_type == "char":
        return 1
    if is_pointer_type(var_type):
        return 4
    raise Exception(f"Runtime error: Unsupported type '{var_type}'.")
```

基本大小規則：

- `int`: 4 bytes
- `char`: 1 byte
- pointer: 4 bytes
- array: `array_length * element_size`

## 變數儲存

一般 scalar 變數：

```c
int x;
char c;
```

對應：

```python
VarSymbol(
    name="x",
    var_type="int",
    addr=0,
    size=4,
    scope_level=0,
)
```

變數的值仍然存在 `memory.py` 的 virtual memory 中，symbol table 只記錄型別、位址與必要 metadata。

## 陣列儲存

陣列 symbol 應記錄元素型別、長度、元素大小與總大小。

```c
int a[3];
char s[10];
```

對應：

```python
VarSymbol(
    name="a",
    var_type="int",
    addr=0,
    size=12,
    scope_level=0,
    is_array=True,
    array_length=3,
    element_size=4,
)
```

陣列行為：

- `arr[i]` 使用 `addr + i * element_size` 計算目標位址。
- array 存取需要透過 `memory.check_bounds()` 做越界檢查。
- array identifier 作為 expression 時支援 decay to pointer。
- `int* p = a;` 合法。
- `char* s = "abc";` 合法，string literal 可視為 char array decay。

## 指標儲存

pointer symbol 本身是一般變數，大小固定 4 bytes。

```c
int* p;
char* s;
```

對應：

```python
VarSymbol(
    name="p",
    var_type="int*",
    addr=100,
    size=4,
    scope_level=0,
)
```

設計原則：

- pointer 指向的實際位址存在 memory 中。
- symbol table 只記錄這個變數是 `int*` 還是 `char*`。
- `&x` 回傳 `x` 的位址與 pointee type。
- `*p` 根據 pointer pointee type 讀取 memory。
- pointer arithmetic 使用 pointee type 決定 stride。

## 函式儲存

函式使用獨立 namespace。

```c
int fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}
```

對應：

```python
FunctionSymbol(
    name="fact",
    return_type="int",
    params=[ParamSymbol("n", "int")],
    body=Block(...),
    line=1,
    is_builtin=False,
)
```

建議將 builtins 也註冊成 `FunctionSymbol(is_builtin=True)`，讓 `FUNCS` 輸出與 function lookup 更一致。

## 建議公開 API

```python
define_var(name, var_type, addr, size, line=None)
define_array(name, var_type, addr, length, element_size, line=None)
define_function(name, return_type, params, body, line=None, is_builtin=False)

lookup_var(name)
lookup_function(name)

push_scope()
pop_scope()
current_scope_level()
reset()

iter_vars(scope="all")
iter_functions(include_builtins=True)
```

## 相容 API

第一階段重構時先保留舊 API，避免一次修改過多檔案：

```python
define(name, var_type, addr)
lookup(name)
```

內部可轉呼叫新 API：

```python
def define(self, name, var_type, addr):
    self.define_var(name, var_type, addr, sizeof_type(var_type))

def lookup(self, name):
    symbol = self.lookup_var(name)
    return {
        "type": symbol.var_type,
        "addr": symbol.addr,
    }
```

等 `interpreter.py`、`main.py` 都改完後，再考慮移除舊 API。

## Scope 設計

scope stack：

```python
self.scopes = [global_scope]
```

函式呼叫流程：

```python
push_scope()
配置參數與區域變數
執行函式 body
pop_scope()
```

規則：

- `scopes[0]` 是 global scope。
- 區域變數可 shadow 外層變數。
- 同一個 scope 內重複宣告變數要報錯。
- `pop_scope()` 不允許移除 global scope。
- 遞迴時每次 function call 都建立新的 scope。

## interpreter.py 後續修改順序

### 1. VarDecl

- scalar 使用 `define_var()`。
- array 使用 `define_array()`。
- pointer 使用 `define_var()`，size 固定 4。
- array initializer 寫入連續 memory。
- string initializer 寫入 char array，必要時補 `\0`。

### 2. Identifier evaluation

- 改用 `lookup_var()`。
- scalar 從 memory 讀值。
- pointer 從 memory 讀位址，回傳 pointer value。
- array identifier 在 expression 中 decay to pointer。

### 3. IndexExpr

- 支援 `arr[i]`。
- 支援 `p[i]`。
- 支援讀取與 assignment 左側寫入。
- array 做 bounds check。
- pointer 若能追蹤來源就 bounds check，否則至少檢查 memory 範圍。

### 4. Address / dereference

- 支援 `&x`。
- 支援 `&arr[i]`。
- 支援 `*p`。
- 支援 `*p = value`。

### 5. Function definition

- parser 新增 function definition AST。
- interpreter 遇到 function definition 時只註冊，不立即執行。
- function body 存進 `FunctionSymbol.body`。

### 6. Function call

- `CallExpr` 先查 function namespace。
- builtins 可透過 `is_builtin=True` 分流到 Python builtins。
- user-defined function 建立新 scope、配置參數、執行 body。
- return 使用 `ReturnSignal(value)` 往外傳。

### 7. VARS / FUNCS

- `VARS` 改用 `iter_vars()`。
- `FUNCS` 改用 `iter_functions()`。
- array 輸出型別、長度、起始位址。
- pointer 輸出型別、變數位址、目前存放的指向位址。
- function 輸出 return type、名稱、參數列表、builtin/user。

## 建議實作階段

### 階段一：只重構 symtable.py

- 新增資料模型。
- 新增 scope stack。
- 新增 var / array / function API。
- 保留 `define()` / `lookup()` 相容 API。
- 確保現有 scalar 變數功能不壞。

### 階段二：接上 array metadata

- `VarDecl.is_array` 使用 `define_array()`。
- 實作 array initializer 寫入 memory。
- `VARS` 能顯示 array。

### 階段三：接上 pointer 與 decay

- pointer 變數讀寫。
- `&`、`*`。
- `int* p = a;`。
- `char* s = "abc";`。

### 階段四：接上 function table

- parser 支援 function definition / return。
- interpreter 註冊 user-defined function。
- `FUNCS` 顯示 builtins 與 user functions。

### 階段五：接上 function call / recursion

- function call scope。
- 參數配置。
- return value。
- 遞迴。

## 驗收測試建議

### Scalar 相容性

```c
int x = 3;
char c = 'A';
x += 2;
```

預期：

- 不破壞現有 `int` / `char` 宣告、讀取、指定。
- `VARS` 可穩定顯示 `x` 與 `c`。

### Array

```c
int a[3] = {1, 2, 3};
a[1] = 9;
printf("%d\n", a[1]);
```

預期：

- `a[1]` 正確讀寫。
- 越界存取能回報錯誤，不產生 Python traceback。

### Pointer / Decay

```c
int a[3] = {1, 2, 3};
int* p = a;
printf("%d\n", *p);
```

預期：

- array identifier 可 decay to pointer。
- `*p` 讀到 `a[0]`。

### Function Namespace

```c
int foo;

int foo() {
    return 7;
}
```

預期：

- 變數 `foo` 與函式 `foo` 可同名。
- `VARS` 顯示變數。
- `FUNCS` 顯示函式。

### Recursion

```c
int fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}
```

預期：

- 函式可註冊。
- 後續接上 call 後可正確遞迴。
- 每次呼叫都有獨立 scope。

## 完成條件

- `symtable.py` 有清楚的 var / array / pointer / function 儲存模型。
- 舊有 `define()` / `lookup()` 在過渡期仍可使用。
- `NEW` 後可透過 `reset()` 清空變數 scope 與 function table。
- `VARS` / `FUNCS` 後續可改用 iterator，不再直接依賴 `.table`。
- 後續 interpreter 實作 array、pointer、function、recursion 時，不需要再大改 symbol table 結構。
