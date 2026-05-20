# symtable.py API 文件

## 概覽

`symtable.py` 提供小型 C 直譯器的**符號表**實作，負責追蹤變數、陣列、指標與使用者定義函式的宣告與查找。

架構分為三層：
1. **型別輔助函式** — 集中處理 C 型別字串的判斷與大小計算
2. **資料模型** — 用具名 class 取代裸 dict，描述每種符號的欄位
3. **符號表 `symtable`** — 管理 scope stack 與函式命名空間

---

## 型別輔助函式

### `is_pointer_type(var_type: str) -> bool`

判斷型別字串是否為指標（以 `*` 結尾）。

```python
is_pointer_type("int*")   # True
is_pointer_type("int")    # False
```

---

### `pointee_type(var_type: str) -> str`

回傳指標型別的目標型別。若傳入非指標型別則拋出例外。

```python
pointee_type("int*")    # "int"
pointee_type("char*")   # "char"
pointee_type("int")     # 拋出 Exception
```

---

### `sizeof_type(var_type: str) -> int`

回傳型別的位元組大小（模擬 32 位元環境）。

| 型別           | 大小（bytes） |
|----------------|--------------|
| `"int"`        | 4            |
| `"char"`       | 1            |
| `"int*"`       | 4            |
| `"char*"`      | 4            |
| 其他           | 拋出 Exception |

---

## 資料模型

### `VarSymbol`

代表一個**變數、陣列或指標**符號。

| 欄位             | 型別        | 說明                             |
|------------------|-------------|----------------------------------|
| `name`           | `str`       | 變數名稱                         |
| `var_type`       | `str`       | C 型別字串（`"int"`, `"char"`, `"int*"`, `"char*"`） |
| `addr`           | `int`       | 虛擬記憶體起始位址               |
| `size`           | `int`       | 佔用的總位元組數                 |
| `scope_level`    | `int`       | 宣告所在的 scope 深度，0 為全域  |
| `is_array`       | `bool`      | 是否為陣列                       |
| `array_length`   | `int\|None` | 陣列長度（僅陣列有效）           |
| `element_size`   | `int\|None` | 單一元素位元組數（僅陣列有效）   |
| `line`           | `int\|None` | 原始碼宣告行號，用於錯誤訊息     |

---

### `ParamSymbol`

代表函式的一個**參數**，僅記錄型別資訊，不佔記憶體位址。

| 欄位        | 型別   | 說明                              |
|-------------|--------|-----------------------------------|
| `name`      | `str`  | 參數名稱                          |
| `var_type`  | `str`  | C 型別字串                        |
| `is_array`  | `bool` | 是否宣告為陣列參數（如 `int a[]`）|

---

### `FunctionSymbol`

代表一個**函式定義**，包含簽名與 AST body。

| 欄位          | 型別              | 說明                                                    |
|---------------|-------------------|---------------------------------------------------------|
| `name`        | `str`             | 函式名稱                                                |
| `return_type` | `str`             | 回傳型別（`"int"`, `"char"`, `"void"`, `"int*"`, `"char*"`） |
| `params`      | `list[ParamSymbol]` | 參數列表                                             |
| `body`        | `object`          | 函式 body 的 AST 節點                                   |
| `line`        | `int\|None`       | 原始碼宣告行號                                          |

---

## 符號表 `symtable`

### 建構子

```python
st = symtable()
```

內部維護兩個命名空間：
- `scopes`：`list[dict]`，scope stack，`scopes[0]` 為全域 scope
- `functions`：`dict[str, FunctionSymbol]`，全域函式表

變數與函式命名空間分開，因此變數與函式可以同名（接近 C 語言行為）。

---

### 變數 API

#### `define_var(name, var_type, addr, line=None) -> VarSymbol`

在目前 scope 宣告一個 scalar 或指標變數。同 scope 內重複宣告視為錯誤。

```python
sym = st.define_var("x", "int", addr=1000, line=5)
```

#### `define_array(name, var_type, addr, length, line=None) -> VarSymbol`

在目前 scope 宣告一個陣列，自動計算總大小並設定陣列 metadata。

- `length` 必須 > 0，否則拋出例外
- `size` = `length × sizeof_type(var_type)`

```python
sym = st.define_array("arr", "int", addr=1004, length=10, line=6)
# sym.size == 40, sym.element_size == 4
```

#### `lookup_var(name) -> VarSymbol`

從最近的 scope 往全域 scope 搜尋（支援內層變數遮蔽外層）。找不到則拋出例外。

```python
sym = st.lookup_var("x")
print(sym.addr)
```

---

### 函式 API

#### `define_function(name, return_type, params, body, line=None) -> FunctionSymbol`

在全域函式表中註冊使用者定義函式。不允許重複定義同名函式。

```python
sym = st.define_function("add", "int", params=[...], body=ast_node, line=1)
```

#### `lookup_function(name) -> FunctionSymbol`

在全域函式表中查找函式。找不到則拋出例外。

```python
fn = st.lookup_function("add")
fn.params   # list[ParamSymbol]
fn.body     # AST 節點
```

---

### Scope 管理

#### `push_scope()`

進入新的區塊 scope（例如函式呼叫或複合語句開始時）。

#### `pop_scope()`

離開目前 scope。全域 scope 不允許被移除，否則拋出例外。

#### `current_scope_level() -> int`

回傳目前 scope 深度，0 為全域。

---

### 重置與迭代

#### `reset()`

清空所有變數 scope 與函式表，供 `NEW` 指令重置執行環境使用。

#### `iter_vars() -> Iterator[VarSymbol]`

產出全域 scope（`scopes[0]`）的所有變數符號，供 `VARS` 指令顯示使用。

#### `iter_functions() -> Iterator[FunctionSymbol]`

產出函式表中所有使用者定義的函式符號。

---

### 向下相容 API（過渡期，日後移除）

這些舊介面讓 `interpreter.py` 與 `main.py` 不需要同步修改，待上層全部改用新 API 後再移除。

| 舊方法             | 等同於                    | 回傳格式                             |
|--------------------|---------------------------|--------------------------------------|
| `define(name, var_type, addr)` | `define_var(...)` | `VarSymbol`（但呼叫端不使用）   |
| `lookup(name)`     | `lookup_var(...)`         | `{"type": ..., "addr": ...}`（dict） |
| `table` (property) | `iter_vars()`             | `{name: {"type": ..., "addr": ...}}` |

---

## 典型使用流程

```python
from symtable import symtable, ParamSymbol

st = symtable()

# 宣告全域變數
st.define_var("g", "int", addr=0)

# 進入函式 scope
st.push_scope()
st.define_var("x", "int", addr=100)
st.define_array("buf", "char", addr=104, length=16)

# 查找變數（從最近 scope 往外找）
sym = st.lookup_var("x")    # 找到 scope level 1 的 x
sym = st.lookup_var("g")    # 找到 scope level 0 的 g

# 離開函式 scope
st.pop_scope()

# 定義函式
params = [ParamSymbol("a", "int"), ParamSymbol("b", "int")]
st.define_function("add", "int", params=params, body=ast_node)

fn = st.lookup_function("add")
```
