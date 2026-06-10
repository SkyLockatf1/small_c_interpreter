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
- `scanf`（目前支援 `%d` / `%c`）
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
- user-defined function call：interpreter 已支援函式表查找、call stack、local scope、參數綁定、return value 與遞迴所需的獨立呼叫環境。
- `return`：parser / interpreter 已支援 `return;` 與 `return expr;`，並檢查 `void` / non-void function 的回傳型別。
- symbol table 作用域接線：變數宣告已使用 `define_var()` / `define_array()`，函式呼叫已使用 `push_scope()` / `pop_scope()`，`VARS` 只顯示全域變數。
- 陣列核心：已支援 `int` / `char` 陣列配置、初始化列表、字串初始化、索引讀寫、複合指定與越界檢查。
- 指標核心：已支援 `&x`、`&arr[i]`、`*p` 讀寫、pointer assignment、pointer arithmetic 與 array-to-pointer decay。
- C-style integer division / modulo：`/`、`%`、`/=`、`%=` 已改為 C-like toward-zero 語意，並檢查除以零。
- built-in / user-defined function 驗證：已統一檢查參數數量與 return type；built-in 參數型別仍由各函式實作檢查。
- `FUNCS`：已可列出使用者函式、行號與 hard-coded built-in function 清單。
- `HELP`：`main.py` 已把 `HELP <command>` 的參數傳給 `repl.HELP(args)`，可顯示摘要與單一指令說明。
- `switch / case / default`：已支援 lexer keyword、AST、case 整數常數表達式、duplicate case/default 檢查、fall-through、`break` 跳出 switch，以及 `continue` 穿透到外層 loop。
- pytest regression tests：已建立 pytest 測試，涵蓋 lexer、interpreter、REPL buffer 與 REPL main 部分流程。
- `LOAD filename`：已可從檔案載入程式緩衝區，並在 dirty buffer 時提示確認；已處理檔案不存在、權限、UTF-8 解碼與一般讀檔錯誤。
- `RUN`：已可合併 buffer、建立乾淨 runtime、載入全域宣告與函式、從 `main()` 執行，並輸出 main return value。
- `scanf`：已支援 `%d` / `%c`，會檢查 `int*` / `char*`，輸入不匹配時回傳成功讀取數量。
- `strcat(char* dest, char* src)`：已實作字串串接，並透過 allocation 邊界檢查避免 buffer overflow。
- 互動模式行號：lexer 已支援 `line_start`，使互動輸入的錯誤行號可對齊 buffer / `LIST` 行號。
- `TRACE ON` / `TRACE OFF`：已支援狀態切換；`RUN` 時會從 `main()` 開始，在每個 statement 執行前輸出 `[line n] <statement>`，使用者函式內部語句也會被追蹤。
- `APPEND` / `EDIT`：已保留使用者輸入的前導空白與縮排，不再用 `.strip()` 清掉程式碼格式。

### 部分完成

- `CHECK`：已接上 lexer/parser，能檢查詞法與語法錯誤且不執行程式；完整語意檢查仍待補。
- string / pointer bounds check：`read_cstring()`、`write_cstring()`、`check_ptr()` 已存在並被多數 built-ins 使用；`scanf(%d/%c)` 與 `strcat` 已接上 pointer / allocation 檢查。若未來新增會寫入字串的功能，仍需確認 buffer 邊界。

---

## 1. P0：會直接卡住驗收的功能

### TODO 1：`RUN` 已完成主要流程

目前 `RUN` 已可從 buffer 執行完整程式的 `main()`。

#### 已完成

- 將整個 `buffer` 合併成完整程式碼字串。
- 每次 `RUN` 都建立乾淨的 `Interpreter()`。
- `RUN` 不沿用前一次執行後的動態記憶體與區域狀態。
- `RUN` 會先 parse 整個 buffer。
- `RUN` 會尋找並執行 `main()`。
- 執行結束後輸出：

```text
Program exited with return value 0.
```

- 預設不輸出 debug 訊息，例如：

```text
AST: ...
func call: ...
```

---

### TODO 2：補完整 `CHECK` 語意檢查

目前 `CHECK` 已接上基礎 lexer/parser 檢查，但尚未完成完整 semantic check。

#### 已完成

- 對整個 buffer 做 lexing。
- 對整個 buffer 做 parsing。
- `CHECK` 不會執行程式。
- 無 lexer/parser 錯誤時輸出：

```text
No errors found.
```

#### 需要完成

- 檢查是否有 `main()`。
- 檢查 function / global variable 是否重複定義。
- 檢查未定義變數與未定義函式。
- 檢查函式呼叫參數數量。
- 檢查 return 型別是否符合函式宣告。
- 檢查 `break` 是否只出現在 loop 或 switch 內。
- 檢查 `continue` 是否只出現在 loop 內。

---

### TODO 3：`LOAD` 已完成

目前 `LOAD` 已可從檔案載入 Small-C 原始碼到程式緩衝區。

#### 已完成

- 讀取指定檔案。
- 將檔案內容按行放入 `buffer`。
- 顯示成功載入的行數。
- 若目前 buffer 有未儲存修改，覆蓋前會提示確認。
- 處理錯誤：
  - 檔案不存在
  - 權限不足
  - UTF-8 解碼錯誤
  - 檔案讀取失敗

---

### TODO 4：`TRACE ON` / `TRACE OFF` 已完成

目前 `TRACE ON` / `TRACE OFF` 已可切換追蹤狀態，並在 `RUN` 執行 `main()` 與使用者函式時輸出逐 statement trace。

#### 已完成

- `TRACE ON` 會設定 `interpreter_instance.trace_enabled = True`。
- `TRACE OFF` 會設定 `interpreter_instance.trace_enabled = False`。
- `NEW` 會建立新的 `Interpreter()`，因此會重置 trace 狀態。
- 每個 statement 執行前輸出類似格式：

```text
[line n] <statement>
```

- `ExpressionStmt` 用來區分「完整 expression statement」與 expression 內部節點，避免 `printf()` 參數、二元運算或函式呼叫實參被誤印成 trace。
- `RUN` 會建立 `trace_source_lines`，用 AST 行號找回 buffer 原始程式碼行。
- `RUN` 載入函式定義與全域宣告時不輸出 trace；從呼叫 `main()` 開始才輸出 trace。

---

### TODO 5：`HELP <command>` 主程式接線已完成

目前 `repl.py` 的 `HELP()` 已可無參數列出摘要，也可接收 command 顯示單一指令說明；`main.py` 已把使用者輸入的 `HELP <command>` 參數傳入。

#### 已完成

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

### TODO 6：`RUN` 的 `main()` 執行流程已完成

parser 已有 `FunctionDef`、parameter list 與 function body parsing，`symtable.py` 也已有 function table API；interpreter 目前已支援 user-defined function call、local scope、argument binding、return value 與遞迴所需的獨立呼叫環境。`RUN` 也已接上從整個 buffer 註冊函式、尋找 `main()` 並執行的流程。

#### 已完成

- Interpreter 已新增：
  - `call_user_function()`
  - call stack / stack frame 回收
  - local scope
  - argument binding
  - return value handling

#### 已完成

- `RUN` 流程應為：
  1. 收集所有 function definitions
  2. 找到 `main`
  3. 呼叫 `main()`
  4. 印出 return value

---

### TODO 7：`return` 核心與 `RUN` return value 顯示已完成

parser 與 interpreter 已支援 `return;` / `return expr;`，並使用 `ReturnSignal(value)` 跳出 function body。`void` function 不可回傳值，`int` / `char` function 必須回傳符合宣告型別的值。

#### 已完成

- AST：

```python
ReturnStmt(expr | None)
```

- Interpreter 使用 `ReturnSignal(value)` 跳出 function body。
- `void` function 不應回傳值。
- `int` / `char` function 應回傳值。
- `main()` 的 return value 已用於：

```text
Program exited with return value X.
```

---

### TODO 8：symbol table 作用域已接上

`symtable.py` 已有 scope stack、`VarSymbol` / `FunctionSymbol`、變數與函式的 define / lookup API，且目前已接到 interpreter 與 REPL 顯示邏輯。

#### 已完成

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

### TODO 9：陣列核心已完成

parser 已有 `IndexExpr`、`InitList`、array declaration parsing，interpreter 已支援陣列配置、讀寫與越界檢查。

#### 已完成

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

### TODO 10：指標、取址與解參考核心已完成

目前 unary `&`、`*p` 解參考、指標指定與基礎指標算術已完成。

#### 已完成

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

### TODO 11：C-style integer division 已完成

Python 的 `//` 對負數是向下取整，但 C 語言整數除法是 toward zero；目前 `/`、`%`、`/=`、`%=` 已改用 C-like `c_div()` / `c_mod()`。

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

#### 已完成

```python
def c_div(left, right):
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient
```

`%` 與 `%=` 已同步使用 `c_mod()`，並檢查除以零。

---

## 3. P2：內建函式與 I/O

### TODO 12：修正與補齊 built-in functions

目前多數必要 built-in functions 已完成；仍有少數缺漏或限制。

#### 已完成

- `atoi(char* str)`：已接收 `char_ptr`，並加入需要 memory 的呼叫路徑。
- `itoa(int value, char* dest)`：已支援十進位轉換，並加入需要 memory 的呼叫路徑。
- `strcmp(char* s1, char* s2)`：已符合 C `strcmp` 的逐字元比較邏輯。
- `strcat(char* dest, char* src)`：已完成串接與 buffer overflow 檢查。
- `scanf(char* fmt, ...)`：已支援 `%d` / `%c`，並檢查 pointer 型別。
- `sizeof_int()` / `sizeof_char()`：已完成。

#### 必須完成

- 尚未實作：

```c
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

- 參數數量：已由 `interpreter.py` 的 built-in signature 外層統一檢查。
- return type：已由 `interpreter.py` 外層統一檢查。
- 參數型別：主要由 `builtins.py` 各函式實作自行檢查。
- pointer 是否有效
- array bounds
- 錯誤時不可顯示 Python traceback

---

### TODO 13：`scanf` 已支援 `%d` / `%c`

已確認需要支援 `scanf`，目前已完成 `%d` / `%c` 的必要範圍。

#### 已完成支援範圍

目前支援：

```c
scanf("%d", &x);
scanf("%c", &ch);
```

- 解析 format string。
- 支援 `%d`：
  - 讀入整數
  - 寫入 `int*`
- 支援 `%c`：
  - 讀入單一字元
  - 寫入 `char*`
- 回傳成功讀入的項目數。
- 參數不是 pointer 時要報 runtime error。

#### 不支援 / 不列入目前範圍

- `%s`
- `%C`
- `%%`
- 跨次 `scanf` 保留未消耗輸入；目前一次 `scanf` 讀取一行。

---

### TODO 14：修正 string / pointer bounds check 設計

目前 `char_ptr` / `int_ptr` 保存目前指標位址 `addr`，實際邊界資訊由 `memory.py` 的 allocation table 管理；`find_allocation()` / `check_ptr()` 可從任意 target address 找到所屬 allocation 並檢查可存取範圍。

#### 已完成

- `read_cstring()`：讀取 C 字串時會限制在 allocation 邊界內，避免讀到相鄰配置區。
- `write_cstring()`：寫入字串時會檢查 `max_len` 與實際 allocation 邊界。
- `strlen`、`strcpy`、`strcmp`、`strcat`、`puts`、`printf`、`memset`、`itoa` 已使用上述檢查機制。
- `scanf(%d/%c)` 已檢查 `int*` / `char*` 型別與可寫入範圍。

#### 需要完成

- 若未來新增會寫入字串的 input 函式，例如 `scanf("%s", buf)`，需同步補 buffer 邊界檢查。

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

### TODO 17：同步 `ABOUT` / README 專案資訊

目前 `ABOUT` 已有 ASCII art、版本、作者與學期資訊；README 的課程資訊表仍保留 TODO，待交付前確認後填入。

#### README 需要確認

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


### TODO 18：修正 `INSERT` 輸入提示與縮排保留

目前 `APPEND` 與 `EDIT` 已可保留縮排；`INSERT` 仍使用 `.strip()`，且提示格式不像作業範例。

#### 建議格式

```text
1>
2>
3>
.
```

#### 需要完成

- `INSERT n` 顯示插入位置對應行號。
- `INSERT` 不要用 `.strip()` 移除程式碼前導空白。
- `APPEND` 若要完全符合範例，可再改成顯示下一行行號。

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

### TODO 20：擴充 regression tests 與 `.sc/.expected` 驗收測試

目前已建立 pytest regression tests，涵蓋 lexer、interpreter、REPL buffer 與 REPL main 部分流程。仍建議補上正式 `.sc/.expected` 測試檔與測試 runner：

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

#### 已完成

- pytest 單元測試已涵蓋：
  - lexer keyword / 錯誤處理
  - interpreter 變數、運算式、控制流程、switch/case、陣列、指標、函式、built-ins 與錯誤路徑
  - REPL buffer 操作
  - REPL main 部分命令輸出

#### 需要完成

- 建立 `.sc/.expected` 驗收測試檔。
- 建立測試 runner，比對程式輸出與 expected。
- 補 `scanf`、`RUN`、`CHECK`、`LOAD` 的整合測試。

---

## 7. 建議實作順序

```text
1. 補完整 CHECK semantic checker
2. 實作 exit(int code)
3. 修 INSERT 提示與縮排保留，並視需求調整 APPEND 行號提示
4. 補 `.sc/.expected` 測試集與 runner
5. 補公開測試 A regression test
6. 補 test_define_repl.sc 與其他整合驗收測試
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
- `CHECK` 不執行程式；完整語意檢查仍待補。
- `RUN` 能執行整段程式。
- `TRACE ON/OFF` 有效果。
- `VARS` 只顯示全域變數。
- `FUNCS` 能顯示使用者函式與 built-in functions。
- `switch / case / default` 可正常執行，且 `case` 只接受整數常數表達式。
- `scanf` 可正常讀入 `%d` / `%c`。
- `sizeof_int()` / `sizeof_char()` 可正常回傳。
- `#define` 可在 REPL 中跨輸入保存。
- 公開測試 A 的主要流程可通過。
