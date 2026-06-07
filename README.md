# Small-C Interpreter

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-In%20Development-orange)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 專案簡介

`Small-C Interpreter` 是一個以 Python 實作的 Small-C 互動式解譯器，目標是作為系統軟體期末專題使用。專案提供類似早期 BASIC 解譯器的 REPL 互動環境，讓使用者可以逐行輸入 Small-C 程式碼，並透過程式緩衝區管理、詞法分析、語法分析、符號表、虛擬記憶體與直譯執行等模組，模擬 C-like 語言的執行流程。

本專案目前仍在開發中，部分作業規格功能尚未完整接上。本文件會誠實標示目前已完成、部分完成與待完成項目，方便後續開發、除錯與期末驗收檢查。

## 課程資訊

| 項目 | 內容 |
|---|---|
| 專案名稱 | Small-C Interpreter |
| 課程 | TODO |
| 學期 | Spring 2026 |
| 作者 | TODO |
| 學號 | TODO |
| 指導教師 | TODO |

## 執行環境

建議使用下列環境執行：

| 項目 | 需求 |
|---|---|
| Python | Python 3.10 以上 |
| 作業系統 | Windows / macOS / Linux |
| 第三方套件 | 目前未使用第三方套件 |

## 快速開始

在專案根目錄執行：

```bash
python main.py
```

在 Linux / macOS 環境也可以使用：

```bash
python3 main.py
```

啟動後會進入 REPL：

```text
sc>
```

## REPL 基本操作

可以直接輸入 Small-C 程式碼：

```c
int x = 10;
int y = 20;
printf("%d\n", x + y);
```

也可以使用環境指令管理程式緩衝區，例如：

```text
sc> APPEND
sc> LIST
sc> SAVE demo.sc
sc> VARS
sc> EXIT
```

環境指令在主程式中會先轉成大寫再比對，因此 `list`、`LIST`、`List` 這類輸入形式會被視為相同指令。

## 環境指令支援狀態

| 指令 | 狀態 | 說明 |
|---|---|---|
| `LIST` | 已實作 | 可列出全部、單行或指定範圍的程式緩衝區內容。 |
| `EDIT` | 已實作 | 可修改指定行；直接按 Enter 會保留原行。 |
| `DELETE` | 已實作 | 可刪除單行或指定範圍。 |
| `INSERT` | 已實作 | 可在指定行前插入多行，以單獨一行 `.` 結束。 |
| `APPEND` | 已實作 | 可在緩衝區尾端追加多行，以單獨一行 `.` 結束。 |
| `SAVE` | 已實作 | 可將目前緩衝區寫入檔案，並處理常見寫檔錯誤。 |
| `NEW` | 已實作 | 可清空 buffer、重建 interpreter、清除 macro 狀態；若有未儲存修改會先提示確認。 |
| `TRACE ON/OFF` | 部分實作 | 可切換 trace 狀態，但尚未完整輸出逐 statement trace。 |
| `VARS` | 已實作 | 可顯示目前全域變數、陣列與指標資訊。 |
| `FUNCS` | 已實作 | 可列出目前 interpreter 內已註冊的使用者函式與 hard-coded built-ins。 |
| `ABOUT` | 部分實作 | 已有 ASCII art 顯示，但專案資訊仍待補齊。 |
| `CLEAR` | 已實作 | 可清除終端畫面。 |
| `QUIT` / `EXIT` | 已實作 | 可離開 REPL。 |
| `LOAD` | 已實作 | 可從檔案載入程式緩衝區，dirty buffer 時會先提示確認。 |
| `RUN` | 已實作 | 會建立乾淨 runtime，載入全域宣告與函式，從 `main()` 執行並輸出 return value。 |
| `CHECK` | 部分實作 | 已做 lexer/parser 檢查且不執行程式；完整語意檢查仍待補。 |
| `HELP` | 已實作 | 支援 `HELP` 指令摘要與 `HELP <command>` 單一指令說明。 |

## Small-C 語言支援狀態

| 類別 | 狀態 | 說明 |
|---|---|---|
| 詞法分析 | 已實作核心功能 | 可將原始碼切成 keyword、identifier、number、hexadecimal、string、char、operator、punctuator 等 token，並保留 token 所在行號供錯誤訊息使用。 |
| 詞法錯誤檢查 | 已實作多數檢查 | 可偵測未結束字串 / 字元常數、非法 escape sequence、未結束區塊註解、不支援的浮點常數，以及非法整數或十六進位 suffix。 |
| 註解 | 已實作 | 支援 `//` 單行註解與非巢狀 `/* ... */` 區塊註解，區塊註解跨行時會維護行號。 |
| `#define` | 部分完成 | 支援簡單十進位整數常數替換，例如 `#define MAX 100` 或 `#define N -1`；同一次 REPL 執行期間可跨輸入保存巨集，`NEW` 會清除巨集狀態。 |
| 變數宣告 | 部分完成 | 支援 `int`、`char`、指標與陣列相關 AST / 執行邏輯。 |
| 運算式 | 部分完成 | 支援多數算術、比較、邏輯、位元與指定運算。 |
| 控制結構 | 部分完成 | Parser 與 interpreter 已有 `if`、`while`、`for`、`do while`、`break`、`continue` 相關結構。 |
| 函式定義 | 部分完成 | Parser、symbol table、interpreter 與 `RUN` main 流程已接上；完整 `CHECK` 語意檢查仍待補。 |
| 遞迴 | 已實作 | Interpreter 已支援獨立 call scope，並有 regression tests。 |
| 陣列 | 部分完成 | 虛擬記憶體支援陣列配置、讀寫與邊界檢查。 |
| 指標 | 部分完成 | 支援模擬位址、解參考、指標讀寫與部分指標算術。 |
| 字串 | 部分完成 | 支援字串常數、`char` 陣列與多數字串 built-ins；`scanf` 目前只支援 `%d` / `%c`。 |

## 內建函式支援狀態

| 函式 | 狀態 |
|---|---|
| `printf` | 已實作基本版本，支援 `%d`、`%s`、`%c`、`%x`、`%%`。 |
| `puts` | 已實作。 |
| `putchar` | 已實作。 |
| `getchar` | 已實作基本版本。 |
| `scanf` | 部分實作，支援 `%d`、`%c`；不支援 `%s`。 |
| `strlen` | 已實作。 |
| `strcpy` | 已實作。 |
| `strcmp` | 已實作。 |
| `strcat` | 已實作。 |
| `abs` | 已實作。 |
| `max` | 已實作。 |
| `min` | 已實作。 |
| `pow` | 已實作。 |
| `sqrt` | 已實作，負數會回報 runtime error。 |
| `mod` | 已實作，除以零會回報 runtime error。 |
| `rand` | 已實作。 |
| `srand` | 已實作。 |
| `memset` | 已實作。 |
| `sizeof_int` | 已實作。 |
| `sizeof_char` | 已實作。 |
| `atoi` | 已實作。 |
| `itoa` | 已實作。 |
| `exit` | 尚未實作；目前僅在 FUNCS / signature 中列出。 |

## 專案架構

| 檔案 | 說明 |
|---|---|
| `main.py` | 程式進入點，包含 REPL 主迴圈、環境指令分派與即時輸入處理。 |
| `repl.py` | REPL 輔助功能，例如 `LIST`、`EDIT`、`DELETE`、`INSERT`、`APPEND`、`SAVE`、`CLEAR`。 |
| `lexer.py` | 詞法分析器，負責將 Small-C 原始碼切成 token。 |
| `parser.py` | 語法分析器與 AST 節點定義，負責建立程式結構。 |
| `interpreter.py` | AST 執行核心，負責變數、運算式、控制流程、函式呼叫與內建函式呼叫。 |
| `memory.py` | 虛擬記憶體，使用 `bytearray` 模擬全域區、堆疊區、指標與陣列存取。 |
| `symtable.py` | 符號表，管理變數、陣列、指標、函式與 scope stack。 |
| `builtins.py` | Small-C 內建函式實作。 |
| `extra_c_type.py` | 額外 C-like 型別包裝，例如 `int_ptr`、`char_ptr`、`array`。 |
| `memory_api.md` | `memory.py` 的 API 文件。 |
| `symtable_api.md` | `symtable.py` 的 API 文件。 |
| `TODO.md` | 開發進度、已知問題與待完成項目。 |

## 目前開發狀態

### 已完成或大致可用

- 基本 REPL 入口與 `sc>` 提示符。
- 單行 Small-C 程式碼的 lex / parse / evaluate 流程。
- 程式緩衝區基本編輯功能。
- `LOAD` / `SAVE` 檔案載入與寫入功能。
- `RUN` 可從 buffer 執行 `main()` 並輸出 return value。
- `CHECK` 已接上 lexer/parser 基礎檢查，且不執行程式。
- 虛擬記憶體配置、讀寫、陣列邊界檢查與指標檢查。
- 符號表 scope stack、變數表與函式表。
- 多數數學與字串相關內建函式。
- `scanf("%d")` / `scanf("%c")`。
- `strcat`。
- pytest regression tests。
- `#define` 簡單數值巨集。
- `int`、`char`、`int*`、`char*` 的部分執行期支援。

### 開發中或尚未完成

- `CHECK` 完整語意檢查。
- 完整 trace 輸出。
- `exit(int code)` 內建函式。
- `.sc/.expected` 驗收測試檔與自動化比對流程。
- `APPEND` / `INSERT` 保留縮排與行號提示格式。
- 啟動畫面與版本資訊仍需補齊。

## 測試方式

目前專案已提供 pytest regression tests，涵蓋 lexer、interpreter、REPL buffer 與 REPL main 部分流程；正式 `.sc/.expected` 驗收測試檔與 runner 仍待補齊。

### Pytest regression tests

建議先分組執行，避免互動測試問題和核心 interpreter 測試混在一起：

```bash
python -m pytest tests/test_interpreter.py -q
python -m pytest tests/test_lexer.py tests/test_repl_buffer.py tests/test_repl_main.py -q
```

### 手動啟動測試

```bash
python main.py
```

確認是否進入：

```text
sc>
```

### 手動 REPL 測試範例

```text
sc> int x = 10;
sc> int y = 20;
sc> printf("%d\n", x + y);
sc> VARS
```

### 程式緩衝區測試範例

```text
sc> APPEND
Enter code to append (or '.' to finish): int main() {
Enter code to append (or '.' to finish):     return 0;
Enter code to append (or '.' to finish): }
Enter code to append (or '.' to finish): .
sc> LIST
sc> SAVE demo.sc
```

### 建議後續 `.sc/.expected` 測試目錄

建議後續補上：

```text
tests/
  01_arithmetic.sc
  01_arithmetic.expected
  02_logic.sc
  02_logic.expected
  03_bitwise.sc
  03_bitwise.expected
  04_variables.sc
  04_variables.expected
  05_builtins.sc
  05_builtins.expected
  06_control.sc
  06_control.expected
  07_loops.sc
  07_loops.expected
  08_array_pointer.sc
  08_array_pointer.expected
  09_recursion.sc
  09_recursion.expected
  10_errors.sc
  10_errors.expected
```

## 已知限制

- `CHECK` 目前主要檢查詞法與語法，尚未完整檢查未定義符號、型別、return、`break` / `continue` 位置等語意錯誤。
- `TRACE ON/OFF` 目前只切換狀態，尚未完整輸出每個 statement 的執行紀錄。
- `scanf` 目前只支援 `%d` / `%c`，不支援 `%s`，且不保留跨次呼叫未消耗輸入。
- `exit(int code)` 尚未實作。
- 目前沒有 `.sc/.expected` 自動化驗收測試器。
- `APPEND` / `INSERT` 目前會移除前導空白，縮排保留仍待修正。
- 啟動時尚未顯示完整歡迎訊息、版本資訊與說明文字。
- 錯誤訊息雖然多處已有處理，但仍需完整測試以避免 Python traceback 洩漏。

## 後續開發 TODO

| 優先度 | 項目 |
|---|---|
| P0 | 補完整 `CHECK` semantic checker。 |
| P1 | 完成 trace statement 輸出。 |
| P1 | 實作 `exit(int code)`。 |
| P1 | 修正 `APPEND` / `INSERT` 提示格式與縮排保留。 |
| P1 | 建立 `.sc/.expected` 驗收測試資料與 runner。 |
| P2 | 補完整專題報告與驗收清單。 |

## 授權

本專案採用 MIT License。詳見 `LICENSE`。
