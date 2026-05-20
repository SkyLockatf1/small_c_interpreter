# Small-C Interactive Interpreter TODO List

## 0. 已知條件、目標與限制

本專案目標是以 Python 實作 Small-C 互動式解譯器，優先通過課程期末專題驗收，而不是擴充成完整 C 語言編譯器。

目前已確認需要支援：

- REPL 互動指令
- Small-C 語言子集
- 內建函式
- 錯誤處理
- `CHECK` / `RUN` / `TRACE` / `VARS` / `FUNCS`
- 陣列、指標、函式、遞迴
- 公開驗收測試 A 的完整流程
- `scanf`
- `sizeof_int()` / `sizeof_char()`
- REPL 中跨輸入保存 `#define`
- `VARS` 只顯示全域變數

目前確認不需要優先支援：

- postfix `i++` / `i--`
- C 語法形式的 `sizeof(x)`

---

## 已確認完成或部分完成項目

### 已完成

- `SAVE filename`：已可將 buffer 寫入檔案，並處理空 buffer、空檔名、權限錯誤、路徑是資料夾與一般寫入錯誤。
- `sizeof_int()` / `sizeof_char()`：已可回傳 `4` / `1`。
- `atoi(char* str)`：已改成 C 風格轉換，支援前導空白、可選正負號、遇到非數字停止，沒有讀到數字時回傳 `0`。
- `itoa(int value, char* str)`：已支援十進位整數轉字串，會寫入結尾 `\0` 並檢查 buffer 大小。
- `strcmp(char* s1, char* s2)`：已改成逐字元比較，包含共同前綴結束時的 `\0` 比較，回傳值邏輯與 C `strcmp` 一致。
- `strlen` / `strcpy` / `puts` / `printf` / `memset`：已接上基本型別檢查與記憶體邊界檢查。
- `symtable.py` 底層 API：已提供 scope stack、function table、變數/陣列/function define 與 lookup API。

### 部分完成

- `TRACE ON` / `TRACE OFF`：指令狀態切換已完成，但尚未實作逐 statement trace 輸出。
- string / pointer bounds check：`read_cstring()`、`write_cstring()`、`check_ptr()` 已存在並被部分 built-ins 使用；`scanf`、`strcat` 與 array decay 的 length 傳遞仍需補齊。

---

## 1. P0：會直接卡住驗收的功能

### TODO 1：完成 `RUN`

目前 `main.py` 中 `RUN` 尚未實作。

#### 需要完成

- 將整個 `buffer` 合併成完整程式碼字串。
- 每次 `RUN` 都建立乾淨的 `Interpreter()`。
- `RUN` 不應沿用前一次執行後的記憶體與符號表。
- `RUN` 應先 parse 整個 buffer。
- `RUN` 應尋找並執行 `main()`。
- 執行結束後輸出：

```text
Program exited with return value 0.
```

- 不應輸出 debug 訊息，例如：

```text
AST: ...
func call: ...
```

---

### TODO 2：完成 `CHECK`

目前 `CHECK` 尚未完整接上。

#### 需要完成

- 對整個 buffer 做 lexing。
- 對整個 buffer 做 parsing。
- 可加入基本語意檢查：
  - 是否有 `main()`
  - function 是否重複定義
  - `break` / `continue` 是否只出現在 loop 內
- `CHECK` 不可執行程式。
- 無錯誤時輸出：

```text
No errors found.
```

---

### TODO 3：完成 `LOAD`

目前 `LOAD` 尚未實作。

#### 需要完成

- 讀取指定檔案。
- 將檔案內容按行放入 `buffer`。
- 顯示成功載入的行數。
- 處理錯誤：
  - 檔案不存在
  - 權限不足
  - 路徑是資料夾
  - 檔案讀取失敗

---

### TODO 4：完成 `TRACE ON` / `TRACE OFF`

目前 `TRACE ON` / `TRACE OFF` 的狀態切換已完成，但逐 statement trace 尚未實作。

#### 已完成

- `TRACE ON` 會設定 `interpreter_instance.trace_enabled = True`。
- `TRACE OFF` 會設定 `interpreter_instance.trace_enabled = False`。
- `NEW` 會建立新的 `Interpreter()`，因此會重置 trace 狀態。

#### 需要完成

- 每個 statement 執行前輸出類似格式：

```text
[line n] <statement>
```

---

### TODO 5：修正 `HELP`

目前 `main.py` 呼叫 `repl.HELP()`，但 `repl.py` 的 `HELP` 定義與內容尚未完成。

#### 需要完成

- 將 `HELP` 改成可無參數呼叫。
- 無參數時列出所有指令。
- 至少包含：

```text
LOAD
SAVE
LIST
EDIT
DELETE
INSERT
APPEND
NEW
RUN
CHECK
TRACE
VARS
FUNCS
HELP
ABOUT
CLEAR
QUIT
EXIT
```

---

## 2. P1：語言核心尚未完成的部分

### TODO 6：實作函式定義、函式表、`main()` 與 user-defined function call

目前 parser 已有 `FunctionDef`、parameter list 與 function body parsing，`symtable.py` 也已有 function table API；但 interpreter 對非 built-in function call 尚未實作，`RUN` 也尚未走完整的 `main()` 執行流程。

#### 需要完成

- Interpreter 新增：
  - `call_user_function()`
  - call stack
  - local scope
  - argument binding
  - return value handling

- `RUN` 流程應為：
  1. 收集所有 function definitions
  2. 找到 `main`
  3. 呼叫 `main()`
  4. 印出 return value

---

### TODO 7：實作 `return`

目前 lexer 有 `return` keyword，但 parser 與 interpreter 尚未完整支援。

#### 需要完成

- 新增 AST：

```python
ReturnStmt(expr | None)
```

- Interpreter 使用 `ReturnSignal(value)` 跳出 function body。
- `void` function 不應回傳值。
- `int` / `char` function 應回傳值。
- `main()` 的 return value 用於：

```text
Program exited with return value X.
```

---

### TODO 8：接上 symbol table 作用域

目前 `symtable.py` 已有 scope stack、`VarSymbol` / `FunctionSymbol`、變數與函式的 define / lookup API；剩下的重點是把這些 API 正式接到 interpreter 與 REPL 顯示邏輯。

#### 需要完成

- interpreter 的變數宣告改用 `define_var()` / `define_array()`。
- function call 時使用 `push_scope()`。
- function return 時使用 `pop_scope()`。
- function parameters 綁定到 local scope。
- block scope 是否要接上，可視驗收需求簡化。

#### `VARS` 規則

- `VARS` 只顯示全域變數。
- 不需要顯示 function local variables。
- local variables 只在函式執行期間存在，除非 trace/debug 另行設計，否則不列入 `VARS`。

---

### TODO 9：完整實作陣列

目前 parser 已有 `IndexExpr`、`InitList`、array declaration parsing，但 interpreter 尚未完整支援陣列配置、讀寫與越界檢查。

#### 需要完成

- 支援：

```c
int arr[10];
char buf[50];
int arr[] = {10, 20, 30};
char s[] = "abc";
```

- `int arr[10]` 分配 `10 * 4` bytes。
- `char buf[50]` 分配 `50 * 1` bytes。
- 實作 `arr[i]` 讀值。
- 實作 `arr[i] = value`。
- 實作 `arr[i] += value` 等複合指定。
- 陣列越界時報 runtime error。
- 不可出現 Python traceback。

---

### TODO 10：完整實作指標、取址與解參考

目前 unary `&` 尚未完成，`*p` 解參考也尚未完整支援。

#### 需要完成

- 支援：

```c
int x;
int *p;
p = &x;
*p = 10;
```

- `&x` 回傳變數地址。
- `&arr[i]` 回傳元素地址。
- `*p` 讀值。
- `*p = value` 寫值。
- `p + 1` / `p - 1` 根據 pointed type 做 stride。
- 陣列傳參時支援 array decay。
- 以下程式必須可執行：

```c
swap(&arr[i], &arr[min_idx]);
```

---

### TODO 11：修正 C-style integer division

目前 Python 的 `//` 對負數是向下取整，但 C 語言整數除法是 toward zero。

#### 問題範例

```c
printf("%d\n", -15 / 4);
```

C 預期結果：

```text
-3
```

Python `//` 會得到：

```text
-4
```

#### 建議修正

```python
def c_div(a, b):
    if b == 0:
        raise Exception("Runtime error: Division by zero")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q
```

`%` 與 `%=` 若要接近 C 語意，也應同步修正。

---

## 3. P2：內建函式與 I/O

### TODO 12：修正與補齊 built-in functions

目前已有部分 built-in functions，但仍有缺漏。

#### 已完成

- `atoi(char* str)`：已接收 `char_ptr`，並加入需要 memory 的呼叫路徑。
- `itoa(int value, char* dest)`：已支援十進位轉換，並加入需要 memory 的呼叫路徑。
- `strcmp(char* s1, char* s2)`：已符合 C `strcmp` 的逐字元比較邏輯。
- `sizeof_int()` / `sizeof_char()`：已完成。

#### 必須完成

- 新增：

```c
scanf(...);
strcat(char* dest, char* src);
exit(int code);
```

#### `sizeof` 支援範圍

- 只需要支援作業規格中的 built-in function：

```c
sizeof_int()
sizeof_char()
```

- 不需要優先支援 C 語法：

```c
sizeof(x)
sizeof(int)
sizeof(char)
```

若之後時間足夠，可以把 `sizeof(...)` 當作加分或重構項目，但不列入目前主要驗收 TODO。

#### Built-in function 檢查項目

所有 built-in function 需要檢查：

- 參數數量
- 參數型別
- pointer 是否有效
- array bounds
- 錯誤時不可顯示 Python traceback

---

### TODO 13：實作 `scanf`

已確認需要支援 `scanf`。

#### 建議支援範圍

先支援驗收最可能出現的格式：

```c
scanf("%d", &x);
scanf("%c", &ch);
scanf("%s", buf);
```

#### 需要完成

- 解析 format string。
- 支援 `%d`：
  - 讀入整數
  - 寫入 `int*`
- 支援 `%c`：
  - 讀入單一字元
  - 寫入 `char*`
- 支援 `%s`：
  - 讀入字串
  - 寫入 char array / `char*`
  - 注意結尾 `\0`
  - 檢查 buffer 是否足夠
- 回傳成功讀入的項目數。
- 參數不是 pointer 時要報 runtime error。

---

### TODO 14：修正 string / pointer bounds check 設計

目前 `char_ptr` / `int_ptr` 已保存 `addr`、`base_addr`、`length`，`memory.py` 也已有 `find_allocation()` / `check_ptr()` 可從任意 target address 找到所屬 allocation。

#### 已完成

- `read_cstring()`：讀取 C 字串時會限制在 allocation 邊界內，避免讀到相鄰配置區。
- `write_cstring()`：寫入字串時會檢查 `max_len` 與實際 allocation 邊界。
- `strlen`、`strcpy`、`strcmp`、`puts`、`printf`、`memset`、`itoa` 已使用上述檢查機制。

#### 需要完成

- 統一尚未完成函式的 bounds check：

```c
strcat
scanf
```

- 修正 interpreter array decay 建立 pointer 時的 length 傳遞，避免 `char_ptr.length` 保持為 `0` 而失去已知 buffer 大小。

---

## 4. P3：REPL 互動與輸出格式

### TODO 15：重構 `main.py` 的 command dispatcher

目前 `main.py` 同時處理：

- REPL command dispatch
- buffer 管理
- interactive code parsing
- interpreter execution

建議拆成 `ReplSession`。

#### 建議結構

```text
main.py
└── ReplSession
    ├── buffer
    ├── interpreter
    ├── trace_enabled
    ├── macro_definitions
    ├── dispatch_command()
    ├── execute_interactive_code()
    ├── run_buffer()
    └── check_buffer()
```

#### 好處

- `RUN`、`CHECK`、互動單行執行可以共用 helper。
- `NEW` 可以集中重置狀態。
- `TRACE`、`VARS`、`FUNCS` 狀態更清楚。
- `#define` 可以在 REPL session 中跨輸入保存。
- 降低 `main.py` 的複雜度。

---

### TODO 16：移除 debug output

目前程式可能會輸出：

```text
AST: ...
func call: ...
```

這會干擾驗收輸出。

#### 需要完成

- 預設不輸出 AST。
- 預設不輸出 function call debug。
- 若需要 debug，使用 debug flag 或 logger。
- 只有 `TRACE ON` 時才輸出 trace 資訊。

---

### TODO 17：修正 `ABOUT` 內容

目前 `ABOUT` 有 ASCII art，但作者、版本、學期仍需要補完整。

#### 需要包含

- Interpreter name
- Version
- Author
- Course
- Semester

#### 範例

```text
Small-C Interactive Interpreter
Version: 1.0
Author: <your name>
Course: System Software
Semester: Spring 2026
```

---


### TODO 18：修正 `APPEND` / `INSERT` 輸入提示

目前 `APPEND` 的提示不像作業範例。

#### 建議格式

```text
1>
2>
3>
.
```

#### 需要完成

- `APPEND` 顯示下一行行號。
- `INSERT n` 顯示插入位置對應行號。
- 不要用 `.strip()` 移除程式碼前導空白。
- 至少要保留縮排，否則 `LIST` 與 demo 會不好看。

---

## 5. P4：Parser / Lexer 細節修正

### TODO 19：整理 `#define` 的生命週期

已確認 `#define` 需要在 REPL 互動模式中跨輸入保存。

#### 需要支援

例如使用者分兩次輸入：

```c
#define SIZE 8
```

再輸入：

```c
int arr[SIZE];
```

`SIZE` 仍然必須有效。

#### 建議設計

- 在 `ReplSession` 中保存 `macro_definitions`。
- `lexer` 可接受外部傳入的 macro table。
- 每次 tokenize 後，新的 `#define` 更新回 session。
- `NEW` 是否清除 macro：
  - 建議清除，因為 `NEW` 應重置狀態。
  - 若老師要求 macro 不清除，再另外調整。

---

## 6. P5：測試與驗收準備

### TODO 20：建立 regression tests

建議建立以下測試檔：

```text
tests/test_repl_commands.sc
tests/test_expr.sc
tests/test_control_flow.sc
tests/test_array_pointer.sc
tests/test_function_recursion.sc
tests/test_builtins.sc
tests/test_errors.sc
tests/test_scanf.sc
tests/test_define_repl.sc
```

#### 每次修改後至少驗證

- REPL 指令
- 算術 / 邏輯 / 位元運算
- 變數宣告與指定
- `CHECK`
- `RUN`
- `TRACE`
- `VARS`
- `FUNCS`
- 控制流程
- 陣列
- 指標
- 函式
- 遞迴
- `scanf`
- `sizeof_int()` / `sizeof_char()`
- REPL 跨輸入 `#define`
- 語法錯誤
- 執行期錯誤

---

## 7. 建議實作順序

```text
1. 修 main.py 指令分派：HELP / DELETE / INSERT / LOAD / CHECK / RUN / TRACE
2. 移除 debug output，修 ABOUT / LIST / APPEND 輸出格式
3. Parser / Interpreter 加 ReturnStmt 與 main() 執行流程
4. Interpreter 加 function table / return signal / user-defined call / recursion
5. 接上 symtable scope API；VARS 只顯示 global
6. 完整實作 array：宣告、初始化、IndexExpr、越界
7. 完整實作 pointer：&、*、pointer assignment、array decay
8. 補 builtins：strcat、scanf、exit，並補齊尚未完成的 bounds check
9. 支援 REPL 跨輸入保存 #define
10. 修 C integer division / modulo
11. 寫公開測試 A regression test
12. 補 test_scanf.sc 與 test_define_repl.sc
```

---

## 8. 已確認決策

### Q1：`scanf` 是否必須實作？

需要。

---

### Q2：哪裡要支援 `sizeof`？

只需要支援作業規格中的 built-in function：

```c
sizeof_int()
sizeof_char()
```

不需要優先支援：

```c
sizeof(x)
sizeof(int)
sizeof(char)
```

---

### Q3：postfix `i++` / `i--` 是否必須支援？

可以不用。

---

### Q4：`#define` 是否需要在互動模式跨行保存？

需要。

例如：

```c
#define SIZE 8
int arr[SIZE];
```

即使兩行是分兩次在 REPL 輸入，`SIZE` 仍應有效。

---

### Q5：`VARS` 顯示範圍為何？

只顯示全域變數。

---

## 9. 最小完成標準

修改完成後至少要滿足：

- `python3 main.py` 可以正常啟動。
- 任一錯誤輸入不會讓 REPL 崩潰。
- 不顯示 Python traceback。
- `NEW` 能清空 buffer、記憶體、符號表、macro definitions 與 trace 狀態。
- `CHECK` 不執行程式。
- `RUN` 能執行整段程式。
- `TRACE ON/OFF` 有效果。
- `VARS` 只顯示全域變數。
- `FUNCS` 能顯示使用者函式與 built-in functions。
- `scanf` 可正常讀入 `%d` / `%c` / `%s`。
- `sizeof_int()` / `sizeof_char()` 可正常回傳。
- `#define` 可在 REPL 中跨輸入保存。
- 公開測試 A 的主要流程可通過。
