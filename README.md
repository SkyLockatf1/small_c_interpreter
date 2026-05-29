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
| `NEW` | 部分實作 | 目前可清空 buffer 並重建 interpreter，但尚未加入未儲存修改確認。 |
| `TRACE ON/OFF` | 部分實作 | 可切換 trace 狀態，但尚未完整輸出逐 statement trace。 |
| `VARS` | 部分實作 | 可顯示目前全域變數、陣列與指標資訊。 |
| `FUNCS` | 部分實作 | 可列出目前 interpreter 內已註冊的使用者函式。 |
| `ABOUT` | 部分實作 | 已有 ASCII art 顯示，但專案資訊仍待補齊。 |
| `CLEAR` | 已實作 | 可清除終端畫面。 |
| `QUIT` / `EXIT` | 已實作 | 可離開 REPL。 |
| `LOAD` | 尚未完成 | `main.py` 中目前仍為 `pass`。 |
| `RUN` | 尚未完成 | `main.py` 中目前仍為 `pass`。 |
| `CHECK` | 尚未完成 | 尚未接上 REPL 指令流程。 |
| `HELP` | 尚未完成 | `repl.py` 中目前仍為空實作。 |

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
| 函式定義 | 部分完成 | Parser、symbol table 與 interpreter 已有函式相關結構，但 REPL `RUN` 尚未完整接上。 |
| 遞迴 | 開發中 | Interpreter 已有 call scope 設計，但需要透過完整 `RUN` 流程驗證。 |
| 陣列 | 部分完成 | 虛擬記憶體支援陣列配置、讀寫與邊界檢查。 |
| 指標 | 部分完成 | 支援模擬位址、解參考、指標讀寫與部分指標算術。 |
| 字串 | 部分完成 | 字串常數與 `char*` 相關內建函式已有部分支援。 |

## 內建函式支援狀態

| 函式 | 狀態 |
|---|---|
| `printf` | 已實作基本版本，支援 `%d`、`%s`、`%c`、`%x`、`%%`。 |
| `puts` | 已實作。 |
| `putchar` | 已實作。 |
| `getchar` | 已實作基本版本。 |
| `scanf` | 尚未完成，目前為空實作。 |
| `strlen` | 已實作。 |
| `strcpy` | 已實作。 |
| `strcmp` | 已實作。 |
| `strcat` | 尚未完成或尚未接上完整流程，需後續確認。 |
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
- `SAVE` 寫檔功能。
- 虛擬記憶體配置、讀寫、陣列邊界檢查與指標檢查。
- 符號表 scope stack、變數表與函式表。
- 多數數學與字串相關內建函式。
- `#define` 簡單數值巨集。
- `int`、`char`、`int*`、`char*` 的部分執行期支援。

### 開發中或尚未完成

- `LOAD` 指令。
- `RUN` 指令。
- `CHECK` 指令。
- `HELP` 指令。
- `scanf` 內建函式。
- 完整 trace 輸出。
- 完整 main function 執行流程。
- 自動化測試目錄與 `.expected` 比對流程。
- 未儲存修改時的覆蓋確認。
- 啟動畫面與版本資訊仍需補齊。

## 測試方式

目前專案尚未提供正式 `tests/` 目錄與 `.sc/.expected` 測試檔。現階段可先使用手動測試方式確認 REPL 與核心模組是否正常。

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

### 建議後續測試目錄

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

- `RUN` 尚未完成，因此完整 `.sc` 程式的載入與從 `main()` 執行流程尚不能作為完成狀態。
- `LOAD` 尚未完成，因此目前無法直接從檔案載入程式緩衝區。
- `CHECK` 尚未完成，因此目前尚無單獨語法 / 語意檢查流程。
- `HELP` 尚未完成。
- `scanf` 尚未實作。
- `TRACE ON/OFF` 目前只切換狀態，尚未完整輸出每個 statement 的執行紀錄。
- 目前沒有正式自動化測試器。
- 啟動時尚未顯示完整歡迎訊息、版本資訊與說明文字。
- 錯誤訊息雖然多處已有處理，但仍需完整測試以避免 Python traceback 洩漏。

## 後續開發 TODO

| 優先度 | 項目 |
|---|---|
| P0 | 完成 `RUN`，支援從 buffer parse 並執行 `main()`。 |
| P0 | 完成 `LOAD`，支援讀取 `.sc` 檔案到 buffer。 |
| P0 | 完成 `CHECK`，支援不執行程式的語法與語意檢查。 |
| P0 | 完成 `HELP`，列出所有 REPL 指令與用法。 |
| P1 | 補齊 `scanf`。 |
| P1 | 完成 trace statement 輸出。 |
| P1 | 建立 `tests/` 測試資料與自動化測試工具。 |
| P1 | 補齊未儲存修改提示。 |
| P2 | 補完整專題報告與驗收清單。 |

## 授權

本專案採用 MIT License。詳見 `LICENSE`。
