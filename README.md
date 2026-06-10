# Small-C Interpreter

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Project](https://img.shields.io/badge/Project-Course%20Project-blueviolet)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 專案簡介

`Small-C Interpreter` 是一個以 Python 實作的 Small-C 互動式解譯器，版本為 `v3.0`。本專案作為系統軟體期末專題，整合詞法分析、語法分析、語意檢查、符號表、虛擬記憶體、AST 直譯執行、內建函式與互動式 REPL 指令，模擬一個 C-like 子集語言的完整執行流程。

使用者可以在 REPL 中逐行輸入 Small-C 程式碼立即執行，也可以透過程式緩衝區載入、編輯、檢查、追蹤與執行完整 `.sc` 原始碼檔案。專案另外提供 Textual TUI 前端，方便以文字介面編輯與執行程式。

## 專案資訊

| 項目 | 內容 |
|---|---|
| 專案名稱 | Small-C Interpreter |
| 版本 | v3.0 |
| 課程 | 系統軟體期末專題 |
| 學期 | Spring 2026 |
| 授權 | MIT License |

## 執行環境

| 項目 | 需求 |
|---|---|
| Python | Python 3.10 以上 |
| 作業系統 | Windows / macOS / Linux |
| CLI REPL 第三方套件 | 無 |
| Textual TUI 第三方套件 | `textual`、`tree-sitter`、`tree-sitter-c` |

## 快速開始

在專案根目錄啟動命令列 REPL：

```bash
python main.py
```

Linux / macOS 也可以使用：

```bash
python3 main.py
```

啟動後會顯示版本資訊並進入 `sc>` 提示符：

```text
======================================
Small-C Interactive Interpreter v3.0
System Software Final Project , Spring 2026
======================================
sc>
```

## Textual TUI

TUI 前端由 `main_tui.py` 提供，會重用既有的 lexer、parser、interpreter 與 repl 模組，並使用 tree-sitter 提供 Small-C/C 語法上色。

安裝相依套件後啟動：

```bash
pip install -r requirements.txt
python main_tui.py
```

不安裝到全域環境時，可使用 `uv`：

```bash
uv run --with textual --with tree-sitter --with tree-sitter-c python main_tui.py
```

語法上色是可選功能；若 tree-sitter 初始化失敗，TUI 編輯器仍可正常使用。

## REPL 使用範例

### 即時執行

可以直接輸入 Small-C 程式碼：

```text
sc> int x = 10;
sc> int y = 20;
sc> printf("%d\n", x + y);
30
```

REPL 會保留全域變數狀態，可使用 `VARS` 查詢：

```text
sc> VARS
int x = 10
int y = 20
```

### 程式緩衝區

也可以用 `APPEND` 建立完整程式，再透過 `CHECK` 與 `RUN` 執行：

```text
sc> APPEND
1> int main() {
2>     printf("Hello Small-C!\n");
3>     return 0;
4> }
5> .
sc> LIST
sc> CHECK
No errors found.
sc> RUN
Hello Small-C!
Program exited with return value 0.
```

環境指令不區分大小寫，例如 `list`、`LIST`、`List` 都會被視為同一個指令。Small-C 語言本身仍依照 C-like 慣例處理大小寫，因此 `value` 與 `Value` 是不同識別字。

## 環境指令

### 程式管理

| 指令 | 功能 |
|---|---|
| `LOAD <filename>` | 從檔案載入 Small-C 原始碼到程式緩衝區；若目前 buffer 有未儲存修改，會先提示確認。 |
| `SAVE <filename>` | 將目前程式緩衝區寫入檔案。 |
| `LIST` | 列出整個程式緩衝區。 |
| `LIST <n>` | 列出第 `n` 行。 |
| `LIST <n1>-<n2>` | 列出第 `n1` 行到第 `n2` 行。 |
| `EDIT <n>` | 修改第 `n` 行；直接按 Enter 會保留原行。 |
| `DELETE <n>` | 刪除第 `n` 行。 |
| `DELETE <n1>-<n2>` | 刪除指定範圍。 |
| `INSERT <n>` | 在第 `n` 行前插入多行，以單獨一行 `.` 結束。 |
| `APPEND` | 在緩衝區尾端追加多行，以單獨一行 `.` 結束。 |
| `NEW` | 清空 buffer、重建 interpreter、清除 macro 狀態；若目前 buffer 有未儲存修改，會先提示確認。 |

### 執行與除錯

| 指令 | 功能 |
|---|---|
| `RUN` | 建立乾淨 runtime，載入全域宣告與函式，從 `main()` 執行目前 buffer。 |
| `CHECK` | 執行 lexer、parser 與 semantic checker，不執行程式。 |
| `TRACE ON` | 開啟 trace 模式；`RUN` 時會在每個 statement 執行前輸出行號與原始語句。 |
| `TRACE OFF` | 關閉 trace 模式。 |
| `VARS` | 顯示目前全域變數、陣列與指標資訊。 |
| `FUNCS` | 列出使用者函式與內建函式 signature。 |

### 系統指令

| 指令 | 功能 |
|---|---|
| `HELP` | 顯示所有可用指令摘要。 |
| `HELP <command>` | 顯示指定指令說明。 |
| `ABOUT` | 顯示解譯器名稱、版本與專案資訊。 |
| `CLEAR` | 清除終端畫面。 |
| `QUIT` / `EXIT` | 結束 REPL；若目前 buffer 有未儲存修改，會先提示確認。 |

## Small-C 語言功能

### 型別與宣告

支援的 Small-C 型別與宣告形式：

```c
int x;
int y = 10;
char ch = 'A';
int arr[20];
char str[80];
int *ptr;
char *cp;
```

支援項目包含：

- `int`、`char`、`int*`、`char*`。
- 函式回傳型別 `int`、`char`、`void`。
- 全域變數、函式區域變數、參數與一維陣列。
- 陣列索引從 `0` 開始，越界時回報 runtime error。
- 字串常數以 C string 形式存入記憶體，並以 `\0` 結尾。

### 常數與註解

支援項目包含：

- 十進位整數，例如 `42`、`-7`。
- 十六進位整數，例如 `0xFF`、`0X0F`。
- 字元常數，例如 `'A'`、`'\n'`。
- 字串常數，例如 `"hello\n"`。
- `//` 單行註解。
- 非巢狀 `/* ... */` 區塊註解。
- 簡單常數巨集，例如 `#define MAX_SIZE 100`。

### 運算式

支援 C-like 優先順序與結合性的主要運算：

| 類別 | 運算子 |
|---|---|
| 函式呼叫與索引 | `()`、`[]` |
| 一元運算 | `-`、`!`、`~`、`*`、`&`、`++`、`--` |
| 乘除餘數 | `*`、`/`、`%` |
| 加減 | `+`、`-` |
| 位移 | `<<`、`>>` |
| 關係運算 | `<`、`<=`、`>`、`>=` |
| 相等運算 | `==`、`!=` |
| 位元運算 | `&`、`^`、`|` |
| 邏輯運算 | `&&`、`||` |
| 指派運算 | `=`、`+=`、`-=`、`*=`、`/=`、`%=` |

`&&` 與 `||` 支援短路求值。除以零、對零取餘、負數平方根、NULL 指標解參考與陣列越界會回報 runtime error。

### 控制結構

支援下列控制流程：

```c
if (...) { ... }
if (...) { ... } else { ... }
if (...) { ... } else if (...) { ... } else { ... }
while (...) { ... }
for (init; condition; update) { ... }
do { ... } while (...);
switch (...) { case 1: ... default: ... }
break;
continue;
return;
return expr;
```

`switch / case / default` 為本專案的延伸功能，支援 `break` 與 C-like fall-through。

### 函式與遞迴

支援函式定義、呼叫、參數傳遞、回傳值與遞迴：

```c
int fibonacci(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    printf("%d\n", fibonacci(10));
    return 0;
}
```

完整程式以 `int main()` 或 `void main()` 作為進入點。互動模式下，未包在函式內的單行或多行 Small-C 程式碼也可以直接執行。

## 內建函式

| 類別 | 函式 |
|---|---|
| 輸入與輸出 | `putchar`、`getchar`、`printf`、`puts`、`scanf` |
| 字串處理 | `strlen`、`strcpy`、`strcmp`、`strcat` |
| 數學函式 | `abs`、`max`、`min`、`pow`、`sqrt`、`mod`、`rand`、`srand` |
| 記憶體與工具 | `memset`、`sizeof_int`、`sizeof_char`、`atoi`、`itoa`、`exit` |

`printf` 支援 `%d`、`%c`、`%s`、`%x`、`%%`。`scanf` 支援 `%d` 與 `%c`，引數需為指標。

## 專案架構

### 核心模組

| 檔案 | 說明 |
|---|---|
| `lexer.py` | 詞法分析器，負責 token 產生、註解處理、字串與字元常數解析、簡單 macro 展開。 |
| `parser.py` | 語法分析器與 AST 節點定義，負責建立宣告、運算式、控制流程、函式與 `switch/case` 結構。 |
| `interpreter.py` | AST 執行核心與 semantic checker，負責運算式求值、控制流程、函式呼叫、內建函式分派與錯誤檢查。 |
| `memory.py` | 虛擬記憶體，使用 `bytearray` 模擬位址、陣列、指標、字串與型別化讀寫。 |
| `symtable.py` | 符號表，管理變數、陣列、指標、函式與 scope stack。 |
| `builtins.py` | 內建函式輔助實作。 |
| `extra_c_type.py` | 額外 C-like 型別包裝，例如 `int_ptr`、`char_ptr`、`array`。 |

### 使用者介面

| 檔案 | 說明 |
|---|---|
| `main.py` | CLI REPL 進入點，包含主迴圈、環境指令分派、即時輸入、`RUN` 與 `CHECK` 流程。 |
| `repl.py` | REPL 輔助功能，實作 buffer 編輯、檔案存取、說明文字與終端工具。 |
| `main_tui.py` | Textual TUI 前端，提供編輯器、輸出區、指令操作與語法上色。 |

### 文件與測試

| 路徑 | 說明 |
|---|---|
| `README.md` | 專案使用說明、功能清單、架構與測試方式。 |
| `memory.md` / `memory_api.md` | 虛擬記憶體設計與 API 說明。 |
| `symtable.md` / `symtable_api.md` | 符號表設計與 API 說明。 |
| `tests/` | pytest regression tests、範例 `.sc` 程式與 acceptance-style 測試資料。 |
| `tests/small_c_test_suite/` | 17 組 `.sc` 與 `.expected` 測試。 |

## 測試方式

### Pytest Regression Tests

執行完整 regression tests：

```bash
python -m pytest
```

也可以分組執行：

```bash
python -m pytest tests/test_interpreter.py -q
python -m pytest tests/test_lexer.py tests/test_repl_buffer.py tests/test_repl_main.py -q
python -m pytest tests/test_check_semantics.py -q
python -m pytest tests/test_tui_frontend.py -q
```

### Small-C Acceptance Test Suite

`tests/small_c_test_suite/` 包含 17 組 `.sc` 與 `.expected`，涵蓋下列功能：

| 類別 | 測試檔 |
|---|---|
| 基本算術與變數 | `01_arithmetic_precedence.sc`、`02_variables_compound.sc`、`16_prefix_postfix_increment.sc`、`17_lvalue_increment_array_pointer.sc` |
| 控制結構 | `03_control_if_for_while.sc`、`04_control_do_break_continue.sc` |
| 函式與遞迴 | `05_functions_calls.sc`、`06_recursion_factorial.sc` |
| 陣列與指標 | `07_arrays_strings.sc`、`08_pointers_swap.sc` |
| switch/case 延伸功能 | `09_switch_case.sc`、`10_switch_fallthrough.sc` |
| 錯誤處理 | `11_error_syntax_missing_semicolon.sc`、`12_error_runtime_division_by_zero.sc`、`13_error_pointer_null_deref.sc`、`14_error_pointer_out_of_bounds.sc`、`15_error_array_out_of_bounds.sc` |

可在 REPL 中手動載入測試：

```text
sc> LOAD tests/small_c_test_suite/01_arithmetic_precedence.sc
sc> CHECK
sc> RUN
```

`.expected` 檔案記錄對應的預期輸出或預期錯誤訊息。

## 支援範圍說明

本專案實作的是課程指定的 Small-C 子集與部分延伸功能，不是完整 C compiler。以下內容不在支援範圍內：

- `float`、`double`、`long`、`short`、`unsigned`。
- `struct`、`union`、`enum`、`typedef`。
- `#include`、條件編譯與函式型 macro。
- 多維陣列與 variable-length array。
- `scanf("%s", ...)` 與完整 C 標準函式庫。
- 完整 C compiler 等級的型別系統與最佳化。

## 授權

本專案採用 MIT License。詳見 `LICENSE`。
