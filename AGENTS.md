# AGENTS.md - Small-C 互動式解譯器測試與驗收條件

本文件由「期末專題 - Small-C 互動式解譯器作業說明」OCR 後整理而成，目的不是逐字轉錄原文，而是把作業規格轉成可執行、可檢查、可驗收的開發準則與測試條件。若本文件與教師原始 PDF 有歧義，應以教師原始 PDF 為最高依據。

---

## 1. 專案目標

本專案必須以 **Python 3.10 以上版本**實作一個 **Small-C 互動式解譯器**。啟動後應提供類似早期 BASIC 解譯器的 REPL 環境，使用者可以逐行輸入 Small-C 程式碼並立即解析、執行，也可以透過內建環境指令載入完整 `.sc` 原始碼檔案後一次執行。

解譯器必須整合以下系統軟體核心能力：

- 詞法分析：辨識 Small-C token。
- 語法分析：解析宣告、表達式、控制結構與函式定義。
- 語意分析：檢查作用域、型別、函式呼叫、陣列與指標使用。
- 符號表管理：管理全域變數、區域變數、函式、內建函式。
- 執行期環境模擬：管理 call stack、記憶體、陣列、指標與函式呼叫。
- 錯誤偵測與回報：提供有意義的語法錯誤、語意錯誤與執行期錯誤訊息。
- 互動式環境：支援程式緩衝區、環境指令、多行輸入、除錯指令與狀態查詢。

---

## 2. 執行方式驗收條件

### 2.1 啟動方式

必須可以使用下列指令直接啟動：

```bash
python3 main.py
```

Windows 環境若使用 `python main.py` 也可以接受，但專案 README 必須清楚說明。

### 2.2 啟動畫面

啟動後必須顯示歡迎訊息、版本資訊與提示符，例如：

```text
Small-C Interactive Interpreter v1.0
System Software Final Project, Spring 2026

Type 'HELP' for a list of commands.

sc>
```

版本號與作者資訊可以不同，但必須具備可識別的解譯器名稱與提示符。

### 2.3 REPL 基本條件

REPL 必須符合下列條件：

- 預設提示符為 `sc>` 或等價提示符。
- 可接受單行 Small-C 語句並立即執行。
- 可偵測多行輸入，例如 `{ ... }`、函式定義、迴圈、條件式、區塊註解尚未結束時，必須繼續等待後續輸入。
- 多行輸入期間必須使用清楚的 continuation prompt，例如 `>`。
- 環境指令不區分大小寫，例如 `RUN`、`run`、`Run` 均應有效。
- 一般 Small-C 語言本身仍依 C-like 語言慣例處理大小寫，變數名稱大小寫應視為不同識別字。

---

## 3. Small-C 語言規格驗收條件

### 3.1 資料型別

必須支援：

| 型別 | 驗收條件 |
|---|---|
| `int` | 有號 32-bit 整數，範圍概念為 `-2147483648` 至 `2147483647`。 |
| `char` | 有號 8-bit 字元，可儲存 ASCII 字元值。 |
| `int *` | 指向 `int` 的模擬指標。 |
| `char *` | 指向 `char` 的模擬指標。 |
| `void` | 僅可作為函式回傳型別，表示無回傳值。 |

不得列為必要支援：

- `float`
- `double`
- `long`
- `short`
- `unsigned`
- `struct`
- `union`
- `enum`
- `typedef`

### 3.2 常數與字面值

必須支援：

- 十進位整數常數，例如 `42`、`-7`。
- 十六進位整數常數，例如 `0xFF`、`0X0F`。
- 字元常數，例如 `'A'`、`'0'`。
- 字元跳脫序列：
  - `\n`
  - `\t`
  - `\0`
  - `\\`
  - `\'`
  - `\"`
- 字串常數，例如 `"hello\n"`。

字串常數必須能用於：

- 內建函式呼叫引數，例如 `printf("value = %d\n", x);`。
- `char` 陣列初始化或字串處理函式。

字串在記憶體中應以 `char` 陣列儲存，並自動附加結尾空字元 `\0`。

### 3.3 宣告規則

必須支援：

```c
int x;
int y = 10;
char ch = 'A';
int arr[20];
char str[80];
int *ptr;
char *cp;
```

驗收條件：

- 全域變數可宣告於所有函式定義之外。
- 不要求支援 block scope 內的新變數宣告，例如 `if`、`while` 區塊內宣告變數不列為必要支援。
- 一維陣列大小必須由整數常數指定。
- 不要求支援 variable-length array。
- 陣列索引從 `0` 開始。
- 陣列越界必須能偵測並回報執行期錯誤。

### 3.4 運算子

必須依照 C-like 優先順序與結合性支援下列運算子。

| 優先順序 | 運算子 | 驗收重點 |
|---:|---|---|
| 1 | 函式呼叫 `()`、陣列索引 `[]` | 後綴運算，最高優先權。 |
| 2 | `-`、`!`、`~`、`*`、`&`、`++`、`--` | 前綴一元運算，右結合。 |
| 3 | `*`、`/`、`%` | 乘除餘數。 |
| 4 | `+`、`-` | 加減。 |
| 5 | `<<`、`>>` | 位移。 |
| 6 | `<`、`<=`、`>`、`>=` | 關係運算。 |
| 7 | `==`、`!=` | 相等與不相等。 |
| 8 | `&` | 位元 AND。 |
| 9 | `^` | 位元 XOR。 |
| 10 | `|` | 位元 OR。 |
| 11 | `&&` | 邏輯 AND，必須支援短路求值。 |
| 12 | `||` | 邏輯 OR，必須支援短路求值。 |
| 13 | `=`、`+=`、`-=`、`*=`、`/=`、`%=` | 指派運算，右結合。 |

補充條件：

- 前綴 `++x`、`--x` 必須支援。
- 後綴 `x++`、`x--` 不列為必要支援，可作為延伸功能。
- 除以零與 `% 0` 必須回報執行期錯誤。
- 邏輯運算結果應以 `0` 表示 false，非 `0` 表示 true，關係與邏輯運算輸出應為 `0` 或 `1`。

### 3.5 控制結構

必須支援：

```c
if (...) { ... }
if (...) { ... } else { ... }
if (...) { ... } else if (...) { ... } else { ... }
while (...) { ... }
for (init; condition; update) { ... }
do { ... } while (...);
break;
continue;
return;
return expr;
```

驗收條件：

- `break` 只能作用於最內層 `while`、`for`、`do while` 迴圈。
- `continue` 只能跳到最內層迴圈的下一次迭代。
- `return` 必須能從目前函式返回。
- `switch / case` 不列為必要功能，可作為加分項目。

### 3.6 函式

必須支援函式定義，例如：

```c
int add(int a, int b) {
    return a + b;
}

void greet() {
    printf("Hello!\n");
}
```

驗收條件：

- 函式回傳型別可為 `int`、`char`、`void`。
- 參數傳遞採 call by value。
- 陣列或指標作為參數時，傳入的是模擬位址或指標值。
- 不要求支援函式前向宣告；函式必須在呼叫前已定義，或由實作在載入時先掃描函式定義後再執行。
- 完整程式必須有 `int main()` 或 `void main()` 作為進入點。
- 在互動模式下，若輸入語句不在任何函式定義內，必須能於全域環境直接執行。
- 必須支援遞迴呼叫，且每次呼叫應有獨立的區域變數與參數環境。

### 3.7 內建函式

必須支援下列內建函式，且 Small-C 程式不需要事先宣告即可呼叫。

#### 3.7.1 輸入與輸出

| 函式 | 驗收條件 |
|---|---|
| `int putchar(int ch)` | 輸出一個字元，回傳該字元整數值。 |
| `int getchar()` | 讀取一個字元；輸入結束時回傳 `-1`。 |
| `void printf(char *fmt, ...)` | 至少支援 `%d`、`%c`、`%s`、`%x`、`%%`，不要求欄位寬度與精度。 |
| `void puts(char *s)` | 輸出字串並自動換行。 |
| `int scanf(char *fmt, ...)` | 至少支援 `%d` 與 `%c`；引數必須為指標；回傳成功讀取項目數。 |

#### 3.7.2 字串處理

| 函式 | 驗收條件 |
|---|---|
| `int strlen(char *s)` | 回傳字串長度，不含結尾 `\0`。 |
| `void strcpy(char *dest, char *src)` | 複製來源字串到目的字串。 |
| `int strcmp(char *s1, char *s2)` | 回傳負數、零或正數。 |
| `void strcat(char *dest, char *src)` | 將來源字串接到目的字串尾端。 |

#### 3.7.3 數學函式

| 函式 | 驗收條件 |
|---|---|
| `int abs(int x)` | 回傳絕對值。 |
| `int max(int a, int b)` | 回傳較大值。 |
| `int min(int a, int b)` | 回傳較小值。 |
| `int pow(int base, int exp)` | `exp >= 0` 時回傳整數次方；`exp < 0` 時回傳 `0`；`exp == 0` 時回傳 `1`。 |
| `int sqrt(int x)` | 回傳平方根整數部分，向下取整；`x < 0` 必須回報執行期錯誤。 |
| `int mod(int a, int b)` | 等同 `a % b`；`b == 0` 必須回報執行期錯誤。 |
| `int rand()` | 回傳 `0` 至 `32767` 的偽隨機整數。 |
| `void srand(int seed)` | 設定偽隨機數種子。 |

#### 3.7.4 記憶體與工具函式

| 函式 | 驗收條件 |
|---|---|
| `void memset(char *ptr, int value, int size)` | 將指定記憶體區塊前 `size` 個位元組設定為 `value`。 |
| `int sizeof_int()` | 回傳 `4`。 |
| `int sizeof_char()` | 回傳 `1`。 |
| `int atoi(char *s)` | 字串轉整數；無有效整數表示時回傳 `0`。 |
| `void itoa(int value, char *str)` | 整數轉十進位字串並存入 `str`。 |
| `void exit(int code)` | 立即終止程式執行並設定結束碼。 |

### 3.8 註解

必須支援：

```c
/* block comment */
// line comment
```

驗收條件：

- `/* ... */` 可跨行。
- `/* ... */` 不要求支援巢狀註解。
- `//` 註解到該行結束。
- 註解不得影響 token 位置與錯誤行號回報。

### 3.9 前處理器

必要支援：

```c
#define MAX_SIZE 100
#define PI_APPROX 3
```

驗收條件：

- 必須支援簡單常數替換。
- 不要求支援含參數巨集，例如 `#define MAX(a,b) ...`。
- 不要求支援 `#include`、`#ifdef`、`#ifndef`、`#endif` 等條件編譯指令。

---

## 4. 互動環境指令驗收條件

所有環境指令均不區分大小寫。

### 4.1 程式管理指令

| 指令 | 必要行為 |
|---|---|
| `LOAD <filename>` | 從檔案載入 Small-C 原始碼到程式緩衝區；成功後顯示讀取行數；若有未儲存修改，覆蓋前須提示確認。 |
| `SAVE <filename>` | 將目前程式緩衝區寫入檔案；成功後顯示寫入行數。 |
| `LIST` | 列出整個程式緩衝區，每行前方顯示行號；空緩衝區需提示。 |
| `LIST <n>` | 列出第 `n` 行。 |
| `LIST <n1>-<n2>` | 列出第 `n1` 行到第 `n2` 行。 |
| `EDIT <n>` | 顯示第 `n` 行，允許輸入新內容取代；直接 Enter 則保留原行。 |
| `DELETE <n>` | 刪除第 `n` 行，其後行號自動遞減。 |
| `DELETE <n1>-<n2>` | 刪除指定範圍。 |
| `INSERT <n>` | 在第 `n` 行前進入插入模式，直到輸入單獨一行 `.` 結束。 |
| `APPEND` | 在緩衝區末尾進入插入模式，直到輸入單獨一行 `.` 結束。 |
| `NEW` | 清除程式緩衝區、全域變數、函式定義與執行期狀態；若有未儲存修改，須提示確認。 |

### 4.2 執行與除錯指令

| 指令 | 必要行為 |
|---|---|
| `RUN` | 對緩衝區程式依序進行詞法分析、語法分析、語意檢查；無錯誤時從 `main()` 執行；執行前應清除前一次 RUN 的動態狀態。 |
| `CHECK` | 僅檢查語法與語意，不實際執行；錯誤與警告須依行號列出；無錯誤時顯示 `No errors found.`。 |
| `TRACE ON` | 開啟追蹤模式；`RUN` 時每個語句執行前顯示行號與語句內容。 |
| `TRACE OFF` | 關閉追蹤模式。 |
| `VARS` | 顯示目前全域變數名稱、型別與值；指標顯示位址；陣列顯示長度與前十個元素。 |
| `FUNCS` | 列出已定義函式名稱、回傳型別、參數列表與起始行號；內建函式以 `[built-in]` 標示。 |

### 4.3 系統指令

| 指令 | 必要行為 |
|---|---|
| `HELP` | 顯示所有可用環境指令摘要。 |
| `HELP <command>` | 顯示指定指令的詳細說明與使用範例。 |
| `ABOUT` | 顯示解譯器名稱、版本、作者資訊與修課學期。 |
| `CLEAR` | 清除終端機畫面。 |
| `QUIT` / `EXIT` | 結束解譯器；若有未儲存修改，須提示確認。 |

---

## 5. 必通測試案例

本節測試案例可拆成 `.sc` 測試程式與 `.expected` 預期輸出，也可用互動腳本測試。所有功能在正式驗收時應以自動化測試優先，手動互動測試作為補充。

### 5.1 測試 01：基本算術與優先順序

輸入：

```c
printf("%d\n", 2 + 3 * 4);
printf("%d\n", (2 + 3) * 4);
printf("%d\n", 100 / 7);
printf("%d\n", 100 % 7);
printf("%d\n", -5 + 3);
printf("%d\n", 2 + 3 * 4 - 8 / 2);
printf("%d\n", ((2 + 3) * (4 - 1)) / 5);
```

預期輸出：

```text
14
20
14
2
-2
10
3
```

驗收重點：

- 乘除優先於加減。
- 括號可改變優先順序。
- 整數除法向零截斷。
- 一元負號正確。

### 5.2 測試 02：關係與邏輯運算

輸入：

```c
printf("%d\n", 5 > 3);
printf("%d\n", 5 < 3);
printf("%d\n", 5 == 5);
printf("%d\n", 5 != 5);
printf("%d\n", 5 >= 5 && 3 < 4);
printf("%d\n", 5 > 10 || 3 < 4);
printf("%d\n", !(5 > 3));
```

預期輸出：

```text
1
0
1
0
1
1
0
```

驗收重點：

- 比較運算輸出 `0` 或 `1`。
- `&&` 與 `||` 必須支援短路求值。
- `!` 邏輯否定正確。

### 5.3 測試 03：位元運算

輸入：

```c
printf("%d\n", 0xFF & 0x0F);
printf("%d\n", 0xA0 | 0x05);
printf("%d\n", 0xFF ^ 0x0F);
printf("%d\n", ~0);
printf("%d\n", 1 << 8);
printf("%d\n", 256 >> 4);
printf("0x%x\n", (0xAB & 0xF0) | 0x0C);
```

預期輸出：

```text
15
165
240
-1
256
16
0xac
```

驗收重點：

- 十六進位常數正確解析。
- 位元 AND、OR、XOR、NOT、左移、右移正確。
- `%x` 以十六進位輸出。

### 5.4 測試 04：變數宣告、指派與 VARS

互動輸入：

```text
sc> int x = 10;
sc> int y = 20;
sc> int z;
sc> z = x + y;
sc> printf("x=%d, y=%d, z=%d\n", x, y, z);
sc> x += 5;
sc> y -= 3;
sc> printf("x=%d, y=%d\n", x, y);
sc> char ch = 'A';
sc> printf("ch=%c (ASCII=%d)\n", ch, ch);
sc> VARS
```

預期輸出至少包含：

```text
x=10, y=20, z=30
x=15, y=17
ch=A (ASCII=65)
int x = 15
int y = 17
int z = 30
char ch = 65 ('A')
```

驗收重點：

- 變數可於互動模式宣告。
- 指派與複合指派正確。
- `char` 可作為 ASCII 整數處理。
- `VARS` 能列出全域狀態。

### 5.5 測試 05：內建數學函式

輸入：

```c
printf("abs(-42) = %d\n", abs(-42));
printf("max(10, 25) = %d\n", max(10, 25));
printf("min(10, 25) = %d\n", min(10, 25));
printf("pow(2, 10) = %d\n", pow(2, 10));
printf("sqrt(144) = %d\n", sqrt(144));
printf("sqrt(150) = %d\n", sqrt(150));
int a = max(abs(-7), min(3, 5));
printf("a = %d\n", a);
printf("pow(2,0)=%d, pow(2,1)=%d, pow(2,-1)=%d\n", pow(2,0), pow(2,1), pow(2,-1));
```

預期輸出：

```text
abs(-42) = 42
max(10, 25) = 25
min(10, 25) = 10
pow(2, 10) = 1024
sqrt(144) = 12
sqrt(150) = 12
a = 7
pow(2,0)=1, pow(2,1)=2, pow(2,-1)=0
```

驗收重點：

- 內建函式可不宣告直接呼叫。
- 巢狀函式呼叫正確。
- `pow` 與 `sqrt` 的邊界條件正確。

### 5.6 測試 06：if / else 條件分支

輸入：

```c
int score = 85;
if (score >= 90) {
    printf("Grade: A\n");
} else if (score >= 80) {
    printf("Grade: B\n");
} else if (score >= 70) {
    printf("Grade: C\n");
} else {
    printf("Grade: F\n");
}

int n = 17;
if (n % 2 == 0) {
    printf("%d is even\n", n);
} else {
    printf("%d is odd\n", n);
}
```

預期輸出：

```text
Grade: B
17 is odd
```

驗收重點：

- `if`、`else if`、`else` 配對正確。
- 條件為非零時視為 true。

### 5.7 測試 07：while 與 for 迴圈

輸入：

```c
int i = 1;
int sum = 0;
while (i <= 100) {
    sum += i;
    i = i + 1;
}
printf("1+2+...+100 = %d\n", sum);

for (i = 1; i <= 9; i = i + 1) {
    printf("%d * %d = %d\n", i, i, i * i);
}
```

預期輸出至少包含：

```text
1+2+...+100 = 5050
1 * 1 = 1
2 * 2 = 4
3 * 3 = 9
4 * 4 = 16
5 * 5 = 25
6 * 6 = 36
7 * 7 = 49
8 * 8 = 64
9 * 9 = 81
```

驗收重點：

- 迴圈初始化、條件、更新皆正確。
- 迴圈終止條件正確。

### 5.8 測試 08：break 與 continue

輸入：

```c
int i;
for (i = 1; i <= 20; i = i + 1) {
    if (i % 3 == 0)
        continue;
    if (i > 15)
        break;
    printf("%d ", i);
}
printf("\n");
```

預期輸出：

```text
1 2 4 5 7 8 10 11 13 14
```

驗收重點：

- `continue` 跳過目前迭代。
- `break` 跳出最內層迴圈。

### 5.9 測試 09：陣列操作

輸入：

```c
int arr[10];
int i;
for (i = 0; i < 10; i = i + 1) {
    arr[i] = (i + 1) * 10;
}
for (i = 0; i < 10; i = i + 1) {
    printf("arr[%d] = %d\n", i, arr[i]);
}
```

預期輸出：

```text
arr[0] = 10
arr[1] = 20
arr[2] = 30
arr[3] = 40
arr[4] = 50
arr[5] = 60
arr[6] = 70
arr[7] = 80
arr[8] = 90
arr[9] = 100
```

驗收重點：

- 陣列配置正確。
- 索引從 `0` 開始。
- 讀寫相同元素應取得一致結果。

### 5.10 測試 10：字串與 char 陣列

輸入：

```c
char name[40];
strcpy(name, "Hello");
printf("name = \"%s\", length = %d\n", name, strlen(name));
strcat(name, " World");
printf("name = \"%s\", length = %d\n", name, strlen(name));
printf("strcmp result: %d\n", strcmp("abc", "abd"));
printf("atoi(\"12345\") = %d\n", atoi("12345"));
```

預期輸出：

```text
name = "Hello", length = 5
name = "Hello World", length = 11
strcmp result: -1
atoi("12345") = 12345
```

驗收重點：

- `char` 陣列可儲存字串。
- 字串結尾 `\0` 正確處理。
- `strlen` 不計入 `\0`。
- `strcpy`、`strcat`、`strcmp`、`atoi` 正確。

### 5.11 測試 11：指標基本操作

輸入：

```c
int x = 42;
int *ptr;
ptr = &x;
printf("x = %d\n", x);
printf("*ptr = %d\n", *ptr);
*ptr = 99;
printf("x = %d\n", x);
printf("ptr points to address %d\n", ptr);
```

預期輸出至少包含：

```text
x = 42
*ptr = 42
x = 99
ptr points to address <integer-address>
```

驗收重點：

- `&` 取得模擬位址。
- `*` 可讀取與寫入指標指向的值。
- 透過指標修改值後，原變數值同步改變。
- 指標位址值不必固定，但必須是可重複使用的有效模擬位址。

### 5.12 測試 12：完整程式、LOAD / CHECK / RUN / SAVE

測試檔：`bubble_sort.sc`

```c
/* Bubble Sort Demo */
void swap(int *a, int *b) {
    int temp;
    temp = *a;
    *a = *b;
    *b = temp;
}

void bubble_sort(int *arr, int n) {
    int i;
    int j;
    for (i = 0; i < n - 1; i = i + 1) {
        for (j = 0; j < n - 1 - i; j = j + 1) {
            if (arr[j] > arr[j + 1]) {
                swap(&arr[j], &arr[j + 1]);
            }
        }
    }
}

void print_array(int *arr, int n) {
    int i;
    for (i = 0; i < n; i = i + 1) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}

int main() {
    int data[8];
    data[0] = 64; data[1] = 25; data[2] = 12; data[3] = 22;
    data[4] = 11; data[5] = 90; data[6] = 45; data[7] = 31;

    printf("Before sorting: ");
    print_array(data, 8);

    bubble_sort(data, 8);

    printf("After sorting: ");
    print_array(data, 8);

    return 0;
}
```

互動驗收流程：

```text
sc> LOAD bubble_sort.sc
sc> LIST
sc> CHECK
sc> RUN
sc> SAVE bubble_sort_copy.sc
```

預期輸出至少包含：

```text
No errors found.
Before sorting: 64 25 12 22 11 90 45 31
After sorting: 11 12 22 25 31 45 64 90
Program exited with return value 0.
```

驗收重點：

- 程式緩衝區可載入、列出、檢查、執行、儲存。
- 函式呼叫、指標參數、陣列傳遞、巢狀迴圈皆正確。

### 5.13 測試 13：遞迴函式

測試檔：`fibonacci.sc`

```c
int fibonacci(int n) {
    if (n == 0) return 0;
    if (n == 1) return 1;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

int main() {
    int i;
    printf("Fibonacci sequence:\n");
    for (i = 0; i < 15; i = i + 1) {
        printf("F(%d) = %d\n", i, fibonacci(i));
    }
    return 0;
}
```

預期輸出：

```text
Fibonacci sequence:
F(0) = 0
F(1) = 1
F(2) = 1
F(3) = 2
F(4) = 3
F(5) = 5
F(6) = 8
F(7) = 13
F(8) = 21
F(9) = 34
F(10) = 55
F(11) = 89
F(12) = 144
F(13) = 233
F(14) = 377
Program exited with return value 0.
```

驗收重點：

- 遞迴呼叫正確。
- 每一層呼叫具有獨立區域變數與參數。
- return value 正確傳回呼叫端。

### 5.14 測試 14：TRACE 追蹤模式

測試檔：`gcd_trace.sc`

```c
int gcd(int a, int b) {
    int temp;
    while (b != 0) {
        temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main() {
    int result;
    result = gcd(48, 18);
    printf("GCD(48, 18) = %d\n", result);
    return 0;
}
```

互動驗收流程：

```text
sc> TRACE ON
sc> RUN
sc> TRACE OFF
```

預期輸出至少包含：

```text
Trace mode enabled.
[line 12] int result;
[line 13] result = gcd(48, 18);
GCD(48, 18) = 6
Program exited with return value 0.
Trace mode disabled.
```

驗收重點：

- `TRACE ON` 後，執行語句前必須顯示行號與語句。
- 函式內部語句也應被追蹤。
- `TRACE OFF` 後不得再輸出追蹤行。

### 5.15 測試 15：EDIT 修改程式

測試流程：

```text
sc> NEW
sc> APPEND
1> int main() {
2>     int i;
3>     int sum = 0;
4>     for (i = 1; i <= 10; i = i + 1) {
5>         sum += i * i;
6>     }
7>     printf("Sum of squares: %d\n", sum);
8>     return 0;
9> }
10> .
sc> RUN
sc> LIST 5
sc> EDIT 5
sc> LIST 4-6
sc> EDIT 7
sc> RUN
```

第一次 `RUN` 預期輸出：

```text
Sum of squares: 385
Program exited with return value 0.
```

將第 5 行修改為：

```c
sum += i * i * i;
```

將第 7 行修改為：

```c
printf("Sum of cubes: %d\n", sum);
```

第二次 `RUN` 預期輸出：

```text
Sum of cubes: 3025
Program exited with return value 0.
```

驗收重點：

- `LIST <n>` 可列出單行。
- `EDIT <n>` 可正確替換指定行。
- 修改後的程式緩衝區可直接重新執行。

### 5.16 測試 16：錯誤偵測與回報

互動輸入與預期錯誤：

| 輸入 | 預期錯誤類型 |
|---|---|
| `int x = 10 / 0;` | Runtime error: division by zero. |
| `int arr[5]; arr[10] = 99;` | Runtime error: array index out of bounds，需包含 index 與 size。 |
| `printf("%d\n", sqrt(-1));` | Runtime error: `sqrt()` argument must be non-negative. |
| `int y =;` | Syntax error，需指出 unexpected token `;` 或 expected expression。 |
| `if (>) {` | Syntax error，需指出 unexpected token `)` 或 expected expression。 |

另測試 `CHECK`：

```c
int main() {
    int x = 10;
    printf("%d\n", x)
    return 0;
}
```

預期 `CHECK` 至少回報：

```text
Error at line 3: expected ';' after expression statement.
1 error(s) found.
```

驗收重點：

- 語法錯誤不得讓解譯器崩潰。
- 執行期錯誤不得造成 Python traceback 直接洩漏給使用者。
- 錯誤訊息應包含錯誤類型與可定位資訊，例如 line number、token、index、size。

### 5.17 測試 17：FUNCS 指令

前置條件：載入 `bubble_sort.sc`。

互動流程：

```text
sc> LOAD bubble_sort.sc
sc> CHECK
sc> FUNCS
```

預期輸出至少包含：

```text
No errors found.
void swap(int *a, int *b) line 2
void bubble_sort(int *arr, int n) line 9
void print_array(int *arr, int n) line 21
int main() line 29
--- built-in functions ---
int putchar(int ch) [built-in]
int getchar() [built-in]
void printf(char *fmt, ...) [built-in]
void puts(char *s) [built-in]
int scanf(char *fmt, ...) [built-in]
int strlen(char *s) [built-in]
void strcpy(char *dest, char *src) [built-in]
int strcmp(char *s1, char *s2) [built-in]
void strcat(char *dest, char *src) [built-in]
int abs(int x) [built-in]
int max(int a, int b) [built-in]
int min(int a, int b) [built-in]
int pow(int base, int exp) [built-in]
int sqrt(int x) [built-in]
int mod(int a, int b) [built-in]
int rand() [built-in]
void srand(int seed) [built-in]
void memset(char *ptr, int value, int size) [built-in]
int sizeof_int() [built-in]
int sizeof_char() [built-in]
int atoi(char *s) [built-in]
void itoa(int value, char *str) [built-in]
void exit(int code) [built-in]
```

驗收重點：

- 使用者自訂函式與內建函式都要列出。
- 自訂函式要顯示回傳型別、參數與行號。

### 5.18 測試 18：完整 Bottom-Up 互動式開發流程

先在互動模式測試質數核心邏輯：

```c
int n = 29;
int i;
int is_prime = 1;
for (i = 2; i * i <= n; i = i + 1) {
    if (n % i == 0) {
        is_prime = 0;
        break;
    }
}
printf("%d is prime: %d\n", n, is_prime);
```

預期輸出：

```text
29 is prime: 1
```

再建立完整程式 `primes.sc`：

```c
int is_prime(int n) {
    int i;
    if (n < 2) return 0;
    for (i = 2; i * i <= n; i = i + 1) {
        if (n % i == 0) return 0;
    }
    return 1;
}

int main() {
    int i;
    int count = 0;
    printf("Prime numbers from 2 to 100:\n");
    for (i = 2; i <= 100; i = i + 1) {
        if (is_prime(i)) {
            printf("%d ", i);
            count = count + 1;
        }
    }
    printf("\nTotal: %d primes\n", count);
    return 0;
}
```

預期輸出：

```text
Prime numbers from 2 to 100:
2 3 5 7 11 13 17 19 23 29 31 37 41 43 47 53 59 61 67 71 73 79 83 89 97
Total: 25 primes
Program exited with return value 0.
```

驗收重點：

- 可由互動片段逐步發展成完整程式。
- 函式、迴圈、條件式、return 與主程式整合正確。
- `SAVE primes.sc` 後應正確寫出檔案。

---

## 6. 測試程式集交付條件

必須至少繳交 **10 個 Small-C 測試程式**，副檔名為 `.sc`，且每個測試程式都必須附對應 `.expected` 預期輸出檔。

測試程式至少涵蓋：

| 類別 | 最少數量 | 必測內容 |
|---|---:|---|
| 基本算術與變數 | 2 | 算術、優先順序、宣告、指派、型別。 |
| 控制結構 | 2 | `if/else`、`while`、`for`、`do while`、`break`、`continue`。 |
| 函式與遞迴 | 2 | 函式定義、參數、return、遞迴、call stack。 |
| 陣列與指標 | 2 | 陣列索引、越界、`&`、`*`、指標參數、字串。 |
| 錯誤處理 | 2 | 語法錯誤、語意錯誤、執行期錯誤。 |

建議測試目錄結構：

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

---

## 7. 專案檔案與模組化驗收條件

建議至少拆成下列模組。實際檔名可不同，但責任必須清楚分離。

| 模組 | 建議責任 |
|---|---|
| `main.py` | 程式進入點，啟動 REPL。 |
| `repl.py` | 互動環境、提示符、多行輸入、環境指令解析。 |
| `lexer.py` | 詞法分析與 token 定義。 |
| `parser.py` | 語法分析與 AST 建構。 |
| `ast.py` 或 `nodes.py` | AST 節點定義。 |
| `interpreter.py` | AST 執行、表達式求值、控制流程。 |
| `symtable.py` | 符號表、作用域、函式表。 |
| `memory.py` | 模擬記憶體、陣列、指標、位址配置。 |
| `builtins.py` | 內建函式實作。 |
| `errors.py` | 自訂錯誤類別與錯誤格式化。 |
| `preprocessor.py` | `#define` 常數替換。 |

必要交付檔案：

```text
main.py
README.md
requirements.txt     # 若無第三方套件，可說明不需要
reports/project_report.pdf
tests/*.sc
tests/*.expected
```

驗收條件：

- 原始碼必須可讀、可維護。
- 命名、縮排、註解需一致。
- 不得把所有功能硬塞在單一巨大檔案中，除非 README 能合理說明。
- 解譯器不得依賴硬編碼測試輸出通過驗收。
- 執行錯誤不得直接顯示未處理的 Python traceback。

---

## 9. 評分與驗收比例

總分 100 分，加分最多額外 15 分。

### 9.1 詞法分析與語法分析：25 分

| 項目 | 分數 |
|---|---:|
| 正確辨識所有 Small-C token | 10 |
| 正確解析變數宣告、表達式、控制結構與函式定義 | 10 |
| 語法錯誤偵測與有意義錯誤訊息 | 5 |

### 9.2 語意分析與執行引擎：30 分

| 項目 | 分數 |
|---|---:|
| 全域與區域變數管理、作用域規則 | 6 |
| 算術、關係、邏輯、位元運算與優先順序 | 6 |
| `if/else`、`while`、`for`、`do while`、`break`、`continue` 正確執行 | 6 |
| 函式呼叫、參數傳遞、回傳值與遞迴 | 6 |
| 陣列與指標操作，包括指標算術 | 6 |

### 9.3 互動環境：20 分

| 項目 | 分數 |
|---|---:|
| REPL 基本運作、多行輸入偵測、持續性狀態管理 | 5 |
| 程式管理指令：`LOAD`、`SAVE`、`LIST`、`EDIT`、`DELETE`、`INSERT`、`APPEND`、`NEW` | 8 |
| 執行與除錯指令：`RUN`、`CHECK`、`TRACE`、`VARS`、`FUNCS` | 5 |
| 系統指令：`HELP`、`ABOUT`、`CLEAR`、`QUIT` / `EXIT` | 2 |

### 9.4 程式品質與文件：15 分

| 項目 | 分數 |
|---|---:|
| 原始碼模組化、命名、縮排、註解品質 | 5 |
| 測試程式集涵蓋範圍與測試設計品質 | 5 |
| 專題報告完整性、清晰度與技術深度 | 5 |

### 9.5 加分項目：最多額外 15 分

| 項目 | 分數 |
|---|---:|
| 支援 `switch / case` | 5 |
| 更完善的執行期錯誤處理，例如除以零、陣列越界、空指標取值 | 5 |
| `#define` 常數替換完整實作 | 5 |

---

## 10. 自動化驗收建議

建議建立測試執行器，例如：

```bash
python3 tools/run_tests.py
```

測試器行為：

1. 啟動 `python3 main.py`。
2. 對每個 `.sc` 測試檔執行：
   - `LOAD tests/xxx.sc`
   - `CHECK`
   - `RUN`
3. 擷取標準輸出。
4. 過濾非決定性內容，例如歡迎訊息、提示符、指標模擬位址。
5. 與 `.expected` 比對。
6. 輸出 pass / fail 報告。

比對規則建議：

- 一般輸出採 exact match。
- 指標位址可採 regex，例如 `ptr points to address \d+`。
- 錯誤訊息可允許少量文字差異，但必須包含錯誤類型與核心原因。
- `rand()` 測試不應要求固定值，除非先呼叫 `srand(seed)` 且規格明確定義演算法。

---

## 11. 常見不合格情形

出現下列情況應視為未通過對應功能驗收：

- 無法以 `python3 main.py` 啟動。
- REPL 輸入錯誤後整個 Python 程式崩潰。
- 語法錯誤顯示 Python traceback，而非 Small-C 錯誤訊息。
- `RUN` 第二次執行時沿用第一次執行殘留的區域變數或執行期狀態。
- `CHECK` 會實際執行程式。
- `LOAD`、`NEW`、`QUIT` 覆蓋未儲存內容時完全沒有提示。
- 陣列越界沒有偵測。
- 除以零沒有偵測。
- 函式呼叫沒有獨立區域變數環境，導致遞迴錯誤。
- `&&`、`||` 沒有短路求值。
- 指標只是印出假位址，但無法透過 `*ptr` 修改原變數。
- 硬編碼範例輸出，而非真正解析與執行 Small-C。

---

## 12. 生成式 AI 使用驗收要求

可以使用 ChatGPT、Claude、GitHub Copilot 等生成式 AI 工具協助開發，但必須符合下列條件：

- 學生必須能理解並解釋自己繳交的程式碼。
- 評分者可使用額外測試程式與互動腳本驗證解譯器，不能只通過公開範例。
- 專題報告中建議說明 AI 工具使用範圍，例如：
  - 哪些模組有使用 AI 協助。
  - AI 產生的程式碼做了哪些修改。
  - 如何驗證 AI 產生的程式碼正確性。
  - 哪些問題最後由學生自行設計解法。
- 無法說明程式碼設計邏輯、模組協作方式或特定功能實作細節者，應視為未達成學習目標。

---

## 13. 最終驗收清單

提交前逐項確認：

- [ ] `python3 main.py` 可啟動。
- [ ] 啟動後有歡迎訊息與 `sc>` 提示符。
- [ ] 單行 Small-C 語句可直接執行。
- [ ] 多行輸入可正確偵測並等待結束。
- [ ] 支援必要資料型別：`int`、`char`、`int *`、`char *`、函式回傳 `void`。
- [ ] 支援十進位、十六進位、字元與字串常數。
- [ ] 支援必要運算子與正確優先順序。
- [ ] 支援 `if/else`、`while`、`for`、`do while`、`break`、`continue`、`return`。
- [ ] 支援函式定義、呼叫、參數、return 與遞迴。
- [ ] 支援陣列、指標、取址、取值與指標參數。
- [ ] 支援全部必要內建函式。
- [ ] 支援 `/* ... */` 與 `//` 註解。
- [ ] 支援簡單 `#define` 常數替換。
- [ ] `LOAD`、`SAVE`、`LIST`、`EDIT`、`DELETE`、`INSERT`、`APPEND`、`NEW` 正常。
- [ ] `RUN`、`CHECK`、`TRACE`、`VARS`、`FUNCS` 正常。
- [ ] `HELP`、`ABOUT`、`CLEAR`、`QUIT`、`EXIT` 正常。
- [ ] 至少 10 個 `.sc` 測試檔與對應 `.expected`。
- [ ] 錯誤處理測試包含語法錯誤、陣列越界、除以零、非法 `sqrt`、缺少分號。
- [ ] 沒有未處理 Python traceback。
- [ ] README 說明執行方式、環境需求與測試方式。
- [ ] 若使用 AI 工具，已在報告中說明使用方式與驗證方式。
