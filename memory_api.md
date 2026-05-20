# memory.py API 文件

## 概覽

`memory.py` 提供小型 C 直譯器的**虛擬記憶體**實作，以一塊連續的 `bytearray` 模擬 32 位元 C 程式的記憶體空間。

### 記憶體佈局

```
位址 0                                              位址 65535
┌──────────────────────────────┬──────────────────────────────┐
│        全域區（global）       │        堆疊區（stack）        │
│  global_top → →              │             ← ← stack_top    │
└──────────────────────────────┴──────────────────────────────┘
```

- **全域區**：從左（位址 0）往右增長，存放全域變數與字串常數
- **堆疊區**：從右（位址 65535）往左縮減，存放區域變數與函式呼叫框架
- 兩區相碰時拋出記憶體耗盡例外

---

## 模組層級輔助

### `_sizeof_type(var_type: str) -> int`

（私用）回傳型別的位元組大小，鏡像 `symtable.sizeof_type`，避免循環 import。

| 型別     | 大小（bytes） |
|----------|--------------|
| `"int"`  | 4            |
| `"char"` | 1            |
| `"int*"` | 4            |
| `"char*"`| 4            |

---

## `VirtualMemory`

### 建構子

```python
vm = VirtualMemory(size=65536)
```

| 參數   | 預設值  | 說明              |
|--------|---------|-------------------|
| `size` | `65536` | 記憶體總大小（bytes） |

**內部狀態欄位**

| 欄位           | 說明                                        |
|----------------|---------------------------------------------|
| `mem`          | `bytearray`，實際記憶體                     |
| `size`         | 記憶體大小                                  |
| `global_top`   | 全域區已使用到的最高位址（下次分配的起點）  |
| `stack_top`    | 堆疊區目前的最低位址（下次分配的終點）      |
| `allocations`  | `dict[addr, size]`，記錄所有活躍的配置      |

---

## int 讀寫

### `set_int(addr, value)`

寫入 32-bit signed int（小端序）。值超出 `[-2³¹, 2³¹-1]` 時自動截斷（wrap-around），不拋 `OverflowError`。

```python
vm.set_int(1000, 42)
vm.set_int(1000, 2**32 + 1)   # 截斷為 1
```

### `get_int(addr) -> int`

讀取 32-bit signed int（小端序）。

```python
val = vm.get_int(1000)   # 42
```

---

## char 讀寫

### `set_char(addr, value)`

寫入 8-bit char，接受整數或單字元字串，自動截斷為低 8 位元。

```python
vm.set_char(500, 65)    # 'A'
vm.set_char(500, 'A')   # 同上
```

### `get_char(addr) -> int`

讀取 8-bit char，回傳有號整數（`-128 ~ 127`）。

```python
val = vm.get_char(500)   # 65
```

---

## 統一讀寫入口

### `read(addr, var_type) -> int`

依型別讀取：`'int'` 呼叫 `get_int`，`'char'` 呼叫 `get_char`。不支援指標型別（指標請用 `get_ptr`）。

```python
val = vm.read(addr, "int")
val = vm.read(addr, "char")
```

### `write(addr, var_type, value)`

依型別寫入：`'int'` 呼叫 `set_int`，`'char'` 呼叫 `set_char`。

```python
vm.write(addr, "int", 100)
vm.write(addr, "char", 65)
```

---

## 指標讀寫

指標統一以 **4-byte unsigned little-endian** 格式儲存，`int*` 與 `char*` 格式相同。

### `get_ptr(addr) -> int`

讀取儲存在 `addr` 的指標值。

```python
ptr_val = vm.get_ptr(addr)
```

### `set_ptr(addr, ptr_val)`

寫入指標值到 `addr`。`ptr_val` 不可為負數。

```python
vm.set_ptr(addr, target_addr)
```

---

## 配置

### `alloc_global(size) -> int`

在全域區（左側）分配 `size` bytes，回傳起始位址。全域區與堆疊區相碰時拋出例外。

```python
addr = vm.alloc_global(4)    # 分配 int
addr = vm.alloc_global(40)   # 分配 int[10]
```

### `alloc_stack(size) -> int`

在堆疊區（右側）分配 `size` bytes，回傳起始位址。先減 `stack_top` 再回傳，避免 off-by-one 問題。

```python
addr = vm.alloc_stack(4)    # 區域 int
```

### `free_stack_frame(frame_entry_top)`

釋放函式進入後的所有 stack allocation，並恢復 `stack_top`。

- `frame_entry_top`：呼叫函式**前**記錄的 `stack_top` 值
- Interpreter 只需在函式進入時記住 `stack_top`，不需要計算 frame size

```python
# 函式呼叫前
saved_top = vm.stack_top

# ... 函式執行，alloc_stack(...)

# 函式返回後
vm.free_stack_frame(saved_top)
```

---

## 陣列元素存取

含邊界檢查，對應 C 的 `arr[i]` 與 `arr[i] = v`。

### `array_read(base_addr, index, elem_type) -> int`

讀取 `base_addr[index]`，stride 由 `elem_type` 決定。

```python
val = vm.array_read(base_addr, 3, "int")    # arr[3]
val = vm.array_read(base_addr, 0, "char")   # buf[0]
```

### `array_write(base_addr, index, elem_type, value)`

寫入 `base_addr[index] = value`。

```python
vm.array_write(base_addr, 3, "int", 99)    # arr[3] = 99
```

---

## 指標算術

### `ptr_add(ptr_val, offset, elem_type) -> int`

計算 `ptr_val + offset * stride`，對應 C 的 `p + n` 或 `p - n`（offset 可為負）。

- stride 由 `_sizeof_type(elem_type)` 決定
- 只驗證結果在 `[0, size)` 範圍內，不強制在同一 allocation 內

```python
new_ptr = vm.ptr_add(ptr_val, 2, "int")    # p + 2 → +8 bytes
new_ptr = vm.ptr_add(ptr_val, -1, "char")  # p - 1 → -1 byte
```

---

## 邊界檢查

### `find_allocation(addr) -> tuple[int, int] | None`

找出包含 `addr` 的 allocation，回傳 `(base_addr, size)` 或 `None`。

- 支援任意中間位址，例如 `p = &arr[3]` 仍能找到 `arr` 的 allocation
- 時間複雜度 O(n)，n = 活躍 allocation 數量

```python
result = vm.find_allocation(ptr_val)
if result:
    base, size = result
```

### `check_ptr(addr, access_size)`

確認 `[addr, addr+access_size)` 落在某個有效的 allocation 內。比 `check_bounds` 更方便，呼叫方不需要知道 `base_addr`。

```python
vm.check_ptr(addr, 4)   # 確認可合法讀寫 4 bytes
```

### `check_bounds(base_addr, target_addr, element_size)` *(向下相容)*

舊 API，確認陣列元素存取不超出 allocation 範圍。`base_addr` 必須是 `allocations` dict 的 key（allocation 的起始位址）。

---

## 字串輔助

### `read_cstring(addr, max_len=4096) -> str`

從 `addr` 讀取 C 字串（讀到 `\0` 為止），回傳 Python `str`。

- 優先用 `find_allocation` 找到所屬 allocation 的邊界作為上限，防止讀入相鄰 allocation 的資料
- 找不到 allocation 時以 `max_len` 作為保護上限
- 字串未正確以 `\0` 結尾時拋出例外

```python
s = vm.read_cstring(ptr_val)
```

### `write_cstring(addr, s, max_len)`

將字串 `s + \0` 寫入 `addr`，total 不超過 `max_len` bytes。超出 buffer 大小時拋出例外（buffer overflow 保護）。供 `scanf("%s")`、`strcpy`、`strcat`、`itoa` 等內建函式使用。

```python
vm.write_cstring(buf_addr, "hello", max_len=16)
```

### `alloc_string(string_content) -> int`

分配全域空間並寫入字串常數（含 `\0`），回傳起始位址。字串字面量具有靜態儲存期，永遠分配在全域區。

```python
addr = vm.alloc_string("hello world")
```

### `set_string(string_content) -> int` *(向下相容)*

`alloc_string` 的舊名 alias，行為完全相同。

---

## 重置

### `reset(size=65536)`

清空記憶體與所有配置紀錄，供 `NEW` 指令重置執行環境時使用。

```python
vm.reset()
```

---

## 典型使用流程

```python
from memory import VirtualMemory

vm = VirtualMemory()

# 分配全域 int
addr = vm.alloc_global(4)
vm.set_int(addr, 42)
print(vm.get_int(addr))   # 42

# 分配全域 char 陣列 buf[16]
buf_addr = vm.alloc_global(16)
vm.array_write(buf_addr, 0, "char", ord('H'))
vm.array_write(buf_addr, 1, "char", ord('i'))
vm.array_write(buf_addr, 2, "char", 0)   # \0 結尾
print(vm.read_cstring(buf_addr))   # "Hi"

# 分配堆疊區域變數
saved_top = vm.stack_top
local_addr = vm.alloc_stack(4)
vm.set_int(local_addr, 99)

# 函式返回後釋放堆疊框架
vm.free_stack_frame(saved_top)

# 分配字串常數
str_addr = vm.alloc_string("hello")
print(vm.read_cstring(str_addr))   # "hello"
```
