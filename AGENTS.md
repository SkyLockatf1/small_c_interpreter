# agents.md

## 目的
本專案是以 Python 撰寫的 Small-C 互動式解譯器。  
目標是完成課程作業要求並通過驗收，不是擴充成完整 C。

## 必須支援的互動指令
解譯器應支援以下指令，且行為穩定：

- `ABOUT`
- `HELP`
- `APPEND`
- `LIST`
- `LIST n`
- `LIST n1-n2`
- `EDIT n`
- `DELETE n`
- `DELETE n1-n2`
- `INSERT n`
- `CHECK`
- `RUN`
- `SAVE filename`
- `NEW`
- `LOAD filename`
- `TRACE ON`
- `TRACE OFF`
- `VARS`
- `FUNCS`
- `CLEAR`
- `QUIT` / `EXIT`

## 必須支援的語言特性
實作時以以下 Small-C 子集為準：

- 基本算術與運算子優先順序
- 關係運算與邏輯運算
- `&&` / `||` 短路求值
- 位元運算
- 變數宣告與指定
- 複合指定（如 `+=`, `-=`, `*=`, `/=`, `%=`）
- `if / else`
- `while`
- `for`
- `do / while`
- `break`
- `continue`
- 一維陣列
- 指標取址與取值（`&`, `*`）
- 函式定義與呼叫
- 遞迴
- 字元與跳脫字元
- 十六進位常數
- `#define` 常數
- 單行與區塊註解

## 必須支援的內建函式類別
至少涵蓋以下類別：

- I/O：如 `printf`, `puts`, `getchar`, `putchar`
- 字串：如 `strlen`, `strcpy`, `strcat`, `strcmp`, `atoi`, `itoa`
- 數學：如 `abs`, `max`, `min`, `pow`, `sqrt`
- 工具：如 `rand`, `srand`, `memset`, `sizeof`

內建函式名稱、參數形式與行為應保持一致，不可任意改名。

## 錯誤處理要求
必須能偵測並回報：

- 語法錯誤
- 除以零
- 非法 `sqrt` 參數
- 陣列越界
- 非法常數、未結束字串、非法跳脫字元、未結束註解等詞法錯誤

發生錯誤時：
- REPL 不可崩潰
- 不可直接顯示 Python traceback
- 應回到提示字元繼續接受輸入

## 執行模型要求
- 明確區分「單行互動執行」與「buffer 的 `CHECK` / `RUN`」
- `CHECK` 只做解析與檢查，不執行程式
- `RUN` 應以整個 buffer 為單位執行，不可只逐行獨立處理
- `RUN` 每次都應從乾淨狀態開始
- `NEW` 應重置 buffer、記憶體、符號表、函式表與 trace 狀態
- `TRACE ON` 時，應能顯示逐步執行資訊

## 目前程式結構
- `main.py`：REPL 入口與指令分派
- `lexer.py`：詞法分析
- `parser.py`：語法分析與 AST
- `interpreter.py`：AST 執行
- `memory.py`：虛擬記憶體與邊界檢查
- `symtable.py`：符號表
- `builtins.py`：內建函式
- `repl.py`：編輯類指令
- `extra_c_type.py`：指標型別輔助類別

## 工作原則
- 先補齊規格，再考慮重構
- 不要加入作業未要求的語言特性
- 每次修改語言功能時，至少同步檢查 `lexer / parser / interpreter`
- `VARS` 與 `FUNCS` 輸出應穩定、可讀、適合驗收
- 以正確性與驗收通過為最高優先
- 以簡潔、清晰、易維護的程式碼為優先
- 不要大量實作後才測試，應該小步快跑、頻繁測試

## 優先補齊項目
若功能尚未完成，優先處理：

- `RUN`
- `CHECK`
- `LOAD`
- `SAVE`
- `TRACE`
- `FUNCS`
- `HELP`
- `for`
- `return`
- 函式定義與呼叫
- `main()`
- 陣列與指標完整支援
- 遞迴
- `break / continue / do-while`

## 測試原則
每次修改後，至少重新驗證：

- REPL 指令
- 算術／邏輯／位元運算
- 變數與內建函式
- `CHECK`、`RUN`、`TRACE`、`VARS`、`FUNCS`
- 控制流程
- 陣列／指標／函式／遞迴
- 語法錯誤與執行期錯誤

## 完成條件
以下條件都成立，修改才算完成：

- `python3 main.py` 可正常啟動
- 單一錯誤輸入不會讓 REPL 崩潰
- `NEW` 能正確重置狀態
- `CHECK` 不執行程式
- `RUN` 可正確執行整段程式
- 受影響功能已重新驗證