# 計畫：重構 memory.py

## Context

目前 `memory.py` 已有基本框架，但有以下問題：
- 4 個指標 set/get 方法（`set_int_ptr` / `get_int_ptr` / `set_char_ptr` / `get_char_ptr`）**定義了但從未被呼叫**。
- `alloc_stack` / `free_stack` **定義了但從未被呼叫**，且 `alloc_stack` 本身有 off-by-one bug。
- `calc_ptr_offset` **定義了但從未被呼叫**。
- `check_bounds` 介面需要呼叫者手動組合三個參數，且無法從任意地址自動找回所屬的 allocation。
- 陣列索引、指標解參考等高頻操作需要呼叫方自己組合多個低階 API，違反「避免過度整合」原則。
- `extra_c_type.py` 的 `char_ptr` 接收 `length` 但沒有儲存；`int_ptr` 完全沒有長度資訊。
- `set_int` 缺乏 32-bit signed 截斷保護，超出範圍時 Python 直接噴 `OverflowError`。

重構目標：**讓 memory.py 的 API 直接對應 Small-C 語法操作**，一個 C 操作對一個 Python 呼叫，不需要呼叫方自己做型別選擇或邊界計算。

---

## 關鍵觀察（現有用法）

| 呼叫方 | 使用的 memory API |
|--------|-----------------|
| `interpreter.py:256` | `alloc_global(size)` |
| `interpreter.py:69` | `set_string(s)` |
| `interpreter.py:97~312` | `get_int`, `set_int`, `get_char`, `set_char` 大量使用 |
| `builtins.py` | `get_char`, `set_char`, `check_bounds` |
| `main.py:214,217` | `get_int`, `get_char`（VARS 顯示） |

**從未被使用的 API**：`alloc_stack`, `free_stack`, `set_int_ptr`, `get_int_ptr`, `set_char_ptr`, `get_char_ptr`, `calc_ptr_offset`

---

## 一、`memory.py` 新設計

### 1.1 Allocation

```python
def alloc_global(self, size: int) -> int
    # 不變，從全域區（左側）往右分配

def alloc_stack(self, size: int) -> int
    # 修正 off-by-one bug：先減 stack_top 再回傳地址
    # 舊：addr = self.stack_top; self.stack_top -= size  →  addr=65536（越界！）
    # 新：self.stack_top -= size; addr = self.stack_top  →  addr=65532（合法）
    # 同時記錄到 allocations

def free_stack_frame(self, frame_entry_top: int)
    # 替換 free_stack(size)
    # frame_entry_top = 函式呼叫「前」的 stack_top 值
    # 清除所有 addr 在 [self.stack_top, frame_entry_top) 範圍內的 allocations 記錄
    # 然後將 self.stack_top 恢復為 frame_entry_top
    # 不需要傳 frame_size，Interpreter 只需在函式進入時記住 stack_top 即可
```

**off-by-one 修正示意**：
```
修正前：stack_top=65536, alloc_stack(4) → addr=65536, stack_top=65532
        → set_int(65536, v) 直接越界（bytearray 最大合法索引 65535）

修正後：stack_top=65536, alloc_stack(4) → stack_top=65532, addr=65532
        → set_int(65532, v) 合法
```

**`free_stack_frame` 邏輯**：
```python
def free_stack_frame(self, frame_entry_top: int):
    to_remove = [a for a in self.allocations if self.stack_top <= a < frame_entry_top]
    for a in to_remove:
        del self.allocations[a]
    self.stack_top = frame_entry_top
```

---

### 1.2 Scalar 讀寫（保留舊 API，新增統一入口，補截斷保護）

```python
# 保留（向下相容，interpreter.py 大量使用）
def get_int(self, addr: int) -> int
def set_int(self, addr: int, value: int)
    # 補上 32-bit signed 截斷，防止 OverflowError：
    # value = (value + 2**31) % 2**32 - 2**31
def get_char(self, addr: int) -> int
def set_char(self, addr: int, value: int)
    # 已有 val & 0xFF 截斷 ✓

# 新增：統一入口，讓 interpreter.py 的型別分派更簡潔
def read(self, addr: int, var_type: str) -> int
    # var_type: 'int' | 'char'
    # 內部呼叫 get_int 或 get_char

def write(self, addr: int, var_type: str, value: int)
    # var_type: 'int' | 'char'
    # 內部呼叫 set_int 或 set_char
```

---

### 1.3 指標讀寫（替換 4 個冗餘方法）

指標值本身就是一個 4-byte unsigned int（地址），不需要區分 `int*` / `char*`。

```python
def get_ptr(self, addr: int) -> int
    # 讀取儲存在 addr 的指標值（4-byte unsigned）
    # 替換 get_int_ptr / get_char_ptr

def set_ptr(self, addr: int, ptr_val: int)
    # 寫入指標值到 addr（無符號 4 bytes）
    # 替換 set_int_ptr / set_char_ptr
```

**移除**：`set_int_ptr`, `get_int_ptr`, `set_char_ptr`, `get_char_ptr`（未被呼叫，直接刪除）

---

### 1.4 陣列元素存取（新增，含邊界檢查）

```python
def array_read(self, base_addr: int, index: int, elem_type: str) -> int
    # C: arr[index]
    # stride = sizeof_type(elem_type)
    # 內部呼叫 check_bounds，再呼叫 get_int 或 get_char

def array_write(self, base_addr: int, index: int, elem_type: str, value: int)
    # C: arr[index] = value
    # 同上，含邊界檢查
```

---

### 1.5 指標算術（替換 calc_ptr_offset）

```python
def ptr_add(self, ptr_val: int, offset: int, elem_type: str) -> int
    # C: p + offset 或 p - offset（offset 可為負）
    # stride = sizeof_type(elem_type)
    #   → elem_type 支援 'int' / 'char' / 'int*' / 'char*'（皆交由 sizeof_type 計算）
    # 只檢查結果地址在 [0, self.size) 範圍內，不強制要求在同一 allocation 內
    # 替換 calc_ptr_offset
```

> **注意**：`sizeof_type` 已在 `symtable.py` 實作，`ptr_add` 直接呼叫即可，不需要自己 if/elif 判斷 stride。

**移除**：`calc_ptr_offset`（替換為 `ptr_add`）

---

### 1.6 字串輔助（新增，供 builtins 使用）

```python
def read_cstring(self, addr: int, max_len: int = 4096) -> str
    # 從 addr 開始讀取直到 \0，回傳 Python str
    # 同時使用 find_allocation 找出所屬 allocation 的邊界，
    # 若讀取超出該 allocation 範圍則報 RuntimeError（防止讀到相鄰 allocation 資料）
    # max_len 作為最後防線，若找不到 allocation 就靠 max_len 保護

def write_cstring(self, addr: int, s: str, max_len: int)
    # 寫入字串 s + '\0' 到 addr，長度含 \0 不得超過 max_len
    # 供 scanf("%s", buf) 使用
    # 內部呼叫 check_bounds / find_allocation 確認不超出 buffer

def alloc_string(self, s: str) -> int
    # 重新命名 set_string，API 不變，**永遠分配到全域區（global region）**
    # 不論 alloc_string 在哪個 scope 被呼叫（函式內或全域），
    # 字串字面量具有 C 語言的靜態儲存期，不放在 stack
    # 舊名 set_string 保留為 alias（向下相容）
```

---

### 1.7 邊界檢查（改善）

```python
def find_allocation(self, addr: int) -> tuple[int, int] | None
    # 給定任意地址（包含 allocation 內部的中間地址），
    # 線性掃描 self.allocations 找出包含該地址的 (base_addr, size)
    # 例：p = &arr[3]，find_allocation(p.addr) 仍能找到 arr 的 allocation
    # 若找不到回傳 None
    # 實作：O(n)，n = 目前活躍的 allocation 數量，對 Small-C 程式無性能問題

def check_ptr(self, addr: int, access_size: int)
    # 確認 [addr, addr+access_size) 在某個有效 allocation 內
    # 內部呼叫 find_allocation
    # 找不到時報 RuntimeError: invalid memory access
    # 取代 builtins 中手工傳 base_addr 的用法

# 舊 check_bounds 保留（向下相容，interpreter / builtins 現有呼叫不需立即改）
def check_bounds(self, base_addr: int, target_addr: int, element_size: int)
```

---

### 1.8 Reset（不變）

```python
def reset(self, size=65536)
    # 不變
```

---

## 二、`extra_c_type.py` 修改

### 問題
- `char_ptr.__init__(addr, length)` 收了 `length` 但沒存。
- `int_ptr` 完全沒有長度，`check_ptr` 無從驗證。

### 修改後

```python
class char_ptr:
    def __init__(self, addr: int, base_addr: int = None, length: int = 0):
        self.addr = addr
        self.base_addr = base_addr if base_addr is not None else addr
        self.length = length      # 緩衝區大小（bytes），0 表示未知

class int_ptr:
    def __init__(self, addr: int, base_addr: int = None, length: int = 0):
        self.addr = addr
        self.base_addr = base_addr if base_addr is not None else addr
        self.length = length

class array:
    # 不變（已有 addr, length, elem_type）
```

`base_addr` 與 `length` 主要供 builtins 進行更精確的邊界檢查，也支援 TODO 15 需求。

---

## 三、其他模組需要修改的地方

### 3.1 `interpreter.py` — 需要修改的點

| 位置 | 舊程式碼 | 修改方向 |
|------|---------|---------|
| `VarDecl`（標量）`line 256` | `alloc_global(size)` | 改為：`alloc_stack` 當 `symtable.current_scope_level() > 0`，否則 `alloc_global` |
| `Identifier` read `line 274-279` | if/elif type dispatch | 可改用 `mem.read(addr, type)` 簡化 |
| `AssignmentExpr` `line 291-312` | 多個 if/elif dispatch | 可改用 `mem.read/write` 簡化 |
| `UnaryExpr &` `line 87-90` | `pass`（未實作） | 從 `symtable.lookup_var(name).addr` 取地址，回傳 `int_ptr` 或 `char_ptr` |
| `UnaryExpr *p` | 尚未實作 | `ptr_val = mem.get_ptr(ptr_sym.addr)`；`mem.read(ptr_val, pointee_type)` |
| `*p = val` | 尚未實作 | `mem.write(ptr_val, pointee_type, val)` |
| `arr[i]`（IndexExpr，base 是 array） | 尚未實作 | `mem.array_read(base_addr, i, elem_type)` |
| `*(p + i)`（IndexExpr，base 是 pointer） | 尚未實作 | `mem.ptr_add(ptr_val, i, elem_type)` 後再 `mem.read` |
| `arr[i] = val` | 尚未實作 | `mem.array_write(base_addr, i, elem_type, val)` |
| `CallExpr`（user func） | `pass`（未實作） | 記錄 `frame_entry_top = memory.stack_top`；push scope；`alloc_stack` 配置 locals；執行 body；`free_stack_frame(frame_entry_top)`；pop scope |
| `VarDecl`（array） | 尚未完整 | `alloc_global(length * elem_size)`，`define_array` |

**Scope 判斷**（補充）：
```python
if self.symtable.current_scope_level() > 0:
    addr = self.memory.alloc_stack(size)
else:
    addr = self.memory.alloc_global(size)
```

**注意**：字串字面量（`parser.String`）呼叫 `alloc_string`，永遠分配到全域區，不受 scope level 影響。

---

### 3.2 `builtins.py` — 需要修改的點

| 函式 | 舊程式碼 | 修改方向 |
|------|---------|---------|
| `puts` `line 20-25` | 手工 `check_bounds` + `get_char` 迴圈 | 改用 `mem.read_cstring(str.addr)` |
| `printf` `line 36-41` | 手工 `check_bounds` + `get_char` 迴圈（format string） | 改用 `mem.read_cstring(fmt.addr)` |
| `printf` `line 70-75` | 手工 `check_bounds` + `get_char` 迴圈（%s argument） | 改用 `mem.read_cstring(args[i].addr)` |
| `memset` `line 158-159` | 直接 `set_char`，無邊界檢查 | 加上 `mem.check_ptr(ptr.addr, num)` 前置檢查 |
| `strlen` `line 163` | 直接 `get_char`，無邊界檢查 | `len(mem.read_cstring(s.addr))` |
| `strcpy` `line 181-187` | 手工 `check_bounds` + `get/set_char` | `mem.write_cstring(dest.addr, mem.read_cstring(src.addr), dest.length)` |
| `strcmp` `line 192-201` | 直接 `get_char` 沒充分 check_bounds | `mem.read_cstring` 讀兩邊再比較 |
| `atoi` `line 173` | 接收 Python `str`，不正確 | 應接收 `char_ptr`，`int(mem.read_cstring(char_str.addr))` |
| 新增 `strcat` | 缺 | `read_cstring` 兩邊，`write_cstring` 到 dest |
| 新增 `itoa` | 缺 | `write_cstring(dest.addr, str(value), dest.length)` |
| 新增 `exit` | 缺 | `raise ExitSignal(code)` 或自訂 signal（由 interpreter 捕捉，避免 Python traceback） |
| 新增 `scanf` | 缺 | 解析 format string；`%d` 讀 int 寫到 `int*`；`%c` 讀 char 寫到 `char*`；`%s` 用 `write_cstring` 寫到 char buffer |

---

### 3.3 `main.py` — 需要修改的點

| 位置 | 舊程式碼 | 修改方向 |
|------|---------|---------|
| VARS `line 206-219` | 只處理 `int` / `char` | 加上 `int*`、`char*`、array 的顯示（用 `symtable.iter_vars()` 取 `VarSymbol`） |
| FUNCS（缺） | 未實作 | 從 `symtable.iter_functions()` 列出使用者函式簽名 |
| RUN `line 181` | `pass` | 建立新 Interpreter，parse buffer，呼叫 main()，印出 exit code |
| CHECK（缺） | 缺 | parse buffer，semantic check，不執行 |
| LOAD `line 185` | `pass` | 讀檔，放進 buffer |
| debug output `line 221, 236` | `print("func call:...")`, `print("AST:...")` | 移除，改為 trace-only（只有 `TRACE ON` 時輸出） |

---

## 四、邊際情況（Review 補充）

| # | 類型 | 問題與對策 |
|---|------|-----------|
| 1 | **Bug** | `alloc_stack` off-by-one：先 `stack_top -= size` 再 `addr = stack_top` |
| 2 | **API 定義** | `free_stack_frame(frame_entry_top)` 只傳呼叫前的 stack_top，內部自行計算範圍 |
| 3 | **實作細節** | `find_allocation` 為 O(n) 線性掃描，Small-C 程式規模下無性能問題 |
| 4 | **Stride** | `ptr_add` 的 stride 呼叫 `sizeof_type(elem_type)`，支援 `'int*'` / `'char*'`（stride=4） |
| 5 | **缺 API** | 新增 `write_cstring(addr, s, max_len)` for `scanf("%s")` 及 `strcpy` / `strcat` / `itoa` |
| 6 | **Correctness** | `set_int` 補 `(v + 2**31) % 2**32 - 2**31` 截斷，防止 Python `OverflowError` |
| 7 | **Bounds 策略** | `read_cstring` 優先用 `find_allocation` 限定讀取範圍，找不到才靠 `max_len` |
| 8 | **字串字面量** | `alloc_string` 永遠用全域區（靜態儲存期），不受 scope level 影響 |
| 9 | **Scope 判斷** | `symtable.current_scope_level() > 0` 決定用 `alloc_stack` 還是 `alloc_global` |

---

## 五、實作建議順序

```
1. memory.py：
   a. 修正 alloc_stack off-by-one
   b. 新增 read()/write() 統一入口；set_int 補截斷
   c. 新增 get_ptr()/set_ptr()，移除 4 個舊指標方法
   d. 新增 array_read()/array_write()
   e. 新增 find_allocation()/check_ptr()
   f. 新增 read_cstring()/write_cstring()，alloc_string 作為 set_string 的新名
   g. 新增 ptr_add()（呼叫 sizeof_type），移除 calc_ptr_offset
   h. 新增 free_stack_frame()，舊 free_stack 可暫時保留為 alias

2. extra_c_type.py：
   a. char_ptr 補存 base_addr, length
   b. int_ptr 補存 base_addr, length

3. interpreter.py：
   a. 移除 debug print（func call、AST）
   b. &x 取址實作（回傳 int_ptr / char_ptr，帶 base_addr + length）
   c. IndexExpr (arr[i]) 讀取 → array_read；*(p+i) → ptr_add + read
   d. AssignmentExpr 左側為 IndexExpr / *p → array_write / write
   e. VarDecl scalar → scope_level 判斷 alloc_global vs alloc_stack
   f. VarDecl array → alloc_global + define_array

4. builtins.py：
   a. puts/printf/strlen/strcmp/strcpy 改用 read_cstring
   b. memset 加 check_ptr
   c. atoi 改接 char_ptr
   d. 新增 strcat, itoa, exit
   e. 新增 scanf（最後，最複雜）

5. main.py：
   a. VARS 補齊 pointer/array 顯示
   b. 移除 debug output
   c. FUNCS 實作
   d. RUN / CHECK / LOAD 實作
```

---

## 六、驗證方式

1. 啟動 `python main.py`，確認 REPL 正常。
2. 輸入 `int x = 5;` → `VARS` 應顯示 `int x = 5`。
3. 輸入 `char buf[8];` → `VARS` 應顯示陣列。
4. 輸入完整 `main()` 函式後 `RUN` → 應輸出 `Program exited with return value 0.`。
5. `CHECK` 不應執行程式，只回報語法/語意錯誤。
6. 任意語法錯誤不應顯示 Python traceback。
7. `int i = 2147483647; i++;` → 應截斷為 `-2147483648`，不應噴 `OverflowError`。
8. `int arr[3]; arr[5] = 1;` → 應報 array index out of bounds，不應 Python traceback。
