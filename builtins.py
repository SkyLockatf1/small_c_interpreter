import math
from memory import VirtualMemory
from extra_c_type import char_ptr

type_mapping = {
    'str': 'char',
    'int': 'int',
    'char_ptr': 'char*',
    'int_ptr': 'int*',
    'None': 'void',
}

def _c_div(left: int, right: int) -> int:
    """C-style integer division: truncate toward zero."""
    quotient = abs(left) // abs(right)
    return -quotient if (left < 0) != (right < 0) else quotient


def _c_mod(left: int, right: int) -> int:
    """C-style remainder: same sign as dividend."""
    return left - _c_div(left, right) * right

# void puts(char* str);
def puts(vm: VirtualMemory, str: char_ptr) -> None:
    if type(str) is not char_ptr:
        got_type = type_mapping.get(type(str).__name__, type(str).__name__)
        raise Exception(f"Runtime error: puts expects char*, got {got_type}")
    # read_cstring 處理邊界與 \0 搜尋，puts 自動換行
    print(vm.read_cstring(str.addr))

# void printf(char* fmt, ...);
def printf(vm: VirtualMemory, fmt: char_ptr, *args) -> None:
    # 簡化版 printf：支援 %%、%d、%s、%c、%x，並檢查參數數量與型別。
    if type(fmt) is not char_ptr:
        got_type = type_mapping.get(type(fmt).__name__, type(fmt).__name__)
        raise Exception(f"Runtime error: printf expects char* for format string, got {got_type}")
    format_str = vm.read_cstring(fmt.addr)
    result = ""
    arg_index = 0  # 目前要使用的可變參數位置。
    i = 0          # 目前正在解析的格式字串位置。
    while i < len(format_str):
        if format_str[i] == '%' and i + 1 < len(format_str):
            # 遇到 % 時，讀取下一個字元判斷格式指定字。
            specifier = format_str[i + 1]
            if specifier == '%':
                result += '%'
                i += 2
            elif specifier == 'd':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is int:
                    result += str(args[arg_index])
                else:
                    got_type = type_mapping.get(type(args[arg_index]).__name__, type(args[arg_index]).__name__)
                    raise Exception(f"Runtime error: printf expects int for %d, got {got_type}")
                arg_index += 1
                i += 2
            elif specifier == 's':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not char_ptr:
                    got_type = type_mapping.get(type(args[arg_index]).__name__, type(args[arg_index]).__name__)
                    raise Exception(f"Runtime error: printf expects char* for %s, got {got_type}")
                # read_cstring 處理邊界驗證，不需要手動逐字元迴圈
                result += vm.read_cstring(args[arg_index].addr)
                arg_index += 1
                i += 2
            elif specifier == 'c':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                value = args[arg_index]
                if type(value) is int and 0 <= value <= 127:
                    result += chr(value)  # %c 僅支援 ASCII 字元碼 0..127。
                elif type(value) is int:
                    raise Exception(f"Runtime error: printf %c expects ASCII code 0..127, got {value}")
                else:
                    got_type = type_mapping.get(type(value).__name__, type(value).__name__)
                    raise Exception(f"Runtime error: printf %c expects int ASCII code 0..127, got {got_type}")
                arg_index += 1
                i += 2
            elif specifier == 'x':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not int:
                    got_type = type_mapping.get(type(args[arg_index]).__name__, type(args[arg_index]).__name__)
                    raise Exception(f"Runtime error: printf expects int for %x, got {got_type}")
                result += format(args[arg_index], 'x')
                arg_index += 1
                i += 2
            else:
                # 不支援的格式指定字照原字元輸出。
                result += format_str[i]
                i += 1
        else:
            result += format_str[i]
            i += 1
    if arg_index != len(args):
        # 格式字串解析完後仍有多餘參數，代表呼叫格式錯誤。
        raise Exception("Runtime error: printf argument count mismatch")
    print(result, end='')

# void scanf(char* fmt, ...);
def scanf(vm: VirtualMemory, fmt: char_ptr, *args) -> None:
    pass  # scanf 的實作較複雜，暫時留空。

# int putchar(int ch);
def putchar(ch: int) -> int:
    if type(ch) is not int:
        got_type = type_mapping.get(type(ch).__name__, type(ch).__name__)
        raise Exception(f"Runtime error: putchar expects int ASCII code 0..127, got {got_type}")
    if ch < 0 or ch > 127:
        raise Exception(f"Runtime error: putchar expects ASCII code 0..127, got {ch}")
    print(chr(ch), end='')
    return ch

# int getchar();
def getchar() -> int:
    ch = input()
    return ord(ch[0]) if ch else -1

# math functions
def abs(x: int) -> int:
    if type(x) is not int:
        got_type = type_mapping.get(type(x).__name__, type(x).__name__)
        raise Exception(f"Runtime error: abs expects int, got {got_type}")
    return x if x >= 0 else -x

def max(a: int, b: int) -> int:
    if type(a) is not int:
        got_type = type_mapping.get(type(a).__name__, type(a).__name__)
        raise Exception(f"Runtime error: max expects int for first argument, got {got_type}")
    if type(b) is not int:
        got_type = type_mapping.get(type(b).__name__, type(b).__name__)
        raise Exception(f"Runtime error: max expects int for second argument, got {got_type}")
    return a if a >= b else b

def min(a: int, b: int) -> int:
    if type(a) is not int:
        got_type = type_mapping.get(type(a).__name__, type(a).__name__)
        raise Exception(f"Runtime error: min expects int for first argument, got {got_type}")
    if type(b) is not int:
        got_type = type_mapping.get(type(b).__name__, type(b).__name__)
        raise Exception(f"Runtime error: min expects int for second argument, got {got_type}")
    return a if a <= b else b

def pow(base: int, exp: int) -> int:
    if type(base) is not int:
        got_type = type_mapping.get(type(base).__name__, type(base).__name__)
        raise Exception(f"Runtime error: pow expects int for base, got {got_type}")
    if type(exp) is not int:
        got_type = type_mapping.get(type(exp).__name__, type(exp).__name__)
        raise Exception(f"Runtime error: pow expects int for exp, got {got_type}")
    return base ** exp if exp >= 0 else 0

def sqrt(x: int) -> int:
    if type(x) is not int:
        got_type = type_mapping.get(type(x).__name__, type(x).__name__)
        raise Exception(f"Runtime error: sqrt expects int, got {got_type}")
    if x < 0:
        raise Exception("Runtime error: sqrt argument must be a non-negative integer")
    return math.floor(x**0.5)

def mod(a: int, b: int) -> int:
    if type(a) is not int:
        got_type = type_mapping.get(type(a).__name__, type(a).__name__)
        raise Exception(f"Runtime error: mod expects int for first argument, got {got_type}")
    if type(b) is not int:
        got_type = type_mapping.get(type(b).__name__, type(b).__name__)
        raise Exception(f"Runtime error: mod expects int for second argument, got {got_type}")
    if b == 0:
        raise Exception("Runtime error: division by zero")
    return _c_mod(a, b)

def rand(rng) -> int:
    if not hasattr(rng, "randint"):
        raise Exception("Runtime error: rand expects RNG with randint")
    return rng.randint(0, 32767)

def srand(rng, seed: int) -> None:
    if not hasattr(rng, "seed"):
        raise Exception("Runtime error: srand expects RNG with seed")
    if type(seed) is not int:
        got_type = type_mapping.get(type(seed).__name__, type(seed).__name__)
        raise Exception(f"Runtime error: srand expects int, got {got_type}")
    rng.seed(seed)

# memory and string functions

# void memset(char* ptr, int value, int num);
def memset(vm: VirtualMemory, ptr: char_ptr, value: int, num: int) -> None:
    if type(ptr) is not char_ptr:
        got_type = type_mapping.get(type(ptr).__name__, type(ptr).__name__)
        raise Exception(f"Runtime error: memset expects char* for ptr, got {got_type}")
    if type(value) is not int:
        got_type = type_mapping.get(type(value).__name__, type(value).__name__)
        raise Exception(f"Runtime error: memset expects int for value, got {got_type}")
    if type(num) is not int:
        got_type = type_mapping.get(type(num).__name__, type(num).__name__)
        raise Exception(f"Runtime error: memset expects int for num, got {got_type}")
    # check_ptr 確認整個 [ptr.addr, ptr.addr+num) 都在合法 allocation 內
    vm.check_ptr(ptr.addr, num)
    for i in range(num):
        vm.set_char(ptr.addr + i, value)

# int strlen(char* str);
def strlen(vm: VirtualMemory, s: char_ptr) -> int:
    if type(s) is not char_ptr:
        got_type = type_mapping.get(type(s).__name__, type(s).__name__)
        raise Exception(f"Runtime error: strlen expects char*, got {got_type}")
    return len(vm.read_cstring(s.addr))

# int sizeof_int();
def sizeof_int() -> int:
    return 4

# int sizeof_char();
def sizeof_char() -> int:
    return 1

# int atoi(char* str);
def atoi(vm: VirtualMemory, char_str: char_ptr) -> int:
    if type(char_str) is not char_ptr:
        got_type = type_mapping.get(type(char_str).__name__, type(char_str).__name__)
        raise Exception(f"Runtime error: atoi expects char*, got {got_type}")

    text = vm.read_cstring(char_str.addr)
    index = 0

    # C atoi 會先略過開頭空白：space、form feed、newline、carriage return、tab、vertical tab。
    while index < len(text) and text[index] in " \f\n\r\t\v":
        index += 1

    # 接著只接受一個可選的正負號；像 "+-12" 或 "- 12" 不會被視為合法數字。
    sign = 1
    if index < len(text) and text[index] in "+-":
        if text[index] == "-":
            sign = -1
        index += 1

    # 從第一個數字開始累積，遇到非數字立即停止，符合 C atoi("12abc") == 12。
    value = 0
    has_digit = False
    while index < len(text) and "0" <= text[index] <= "9":
        has_digit = True
        value = value * 10 + (ord(text[index]) - ord("0"))
        index += 1

    # C atoi 在沒有讀到任何數字時回傳 0，而不是丟出錯誤。
    if not has_digit:
        return 0
    return sign * value

# void itoa(int value, char* str);
def itoa(vm: VirtualMemory, value: int, char_str: char_ptr) -> None:
    if type(value) is not int:
        got_type = type_mapping.get(type(value).__name__, type(value).__name__)
        raise Exception(f"Runtime error: itoa expects int for value, got {got_type}")
    if type(char_str) is not char_ptr:
        got_type = type_mapping.get(type(char_str).__name__, type(char_str).__name__)
        raise Exception(f"Runtime error: itoa expects char* for str, got {got_type}")
    # 先將整數轉為字串，然後寫入 char_str 指向的記憶體位置，最後加上結束符號 '\0'。
    # 寫入範圍由 VirtualMemory.check_ptr() 依 allocation 邊界驗證。
    s = str(value)
    vm.write_cstring(char_str.addr, s, len(s) + 1)

# void strcpy(char* dest, char* src);
def strcpy(vm: VirtualMemory, dest: char_ptr, src: char_ptr) -> None:
    if type(dest) is not char_ptr:
        got_type = type_mapping.get(type(dest).__name__, type(dest).__name__)
        raise Exception(f"Runtime error: strcpy expects char* for dest, got {got_type}")
    if type(src) is not char_ptr:
        got_type = type_mapping.get(type(src).__name__, type(src).__name__)
        raise Exception(f"Runtime error: strcpy expects char* for src, got {got_type}")
    s = vm.read_cstring(src.addr)
    # 寫入範圍由 VirtualMemory.check_ptr() 依 allocation 邊界驗證。
    vm.write_cstring(dest.addr, s, len(s) + 1)

# int strcmp(char* s1, char* s2);
def strcmp(vm: VirtualMemory, s1: char_ptr, s2: char_ptr) -> int:
    if type(s1) is not char_ptr:
        got_type = type_mapping.get(type(s1).__name__, type(s1).__name__)
        raise Exception(f"Runtime error: strcmp expects char* for s1, got {got_type}")
    if type(s2) is not char_ptr:
        got_type = type_mapping.get(type(s2).__name__, type(s2).__name__)
        raise Exception(f"Runtime error: strcmp expects char* for s2, got {got_type}")
    str1 = vm.read_cstring(s1.addr)
    str2 = vm.read_cstring(s2.addr)
    # 逐字元比較，包含共同前綴結束時的 '\0'，使回傳值與 C strcmp 一致。
    index = 0
    while index < len(str1) and index < len(str2):
        diff = ord(str1[index]) - ord(str2[index])
        if diff != 0:
            return diff
        index += 1
    # 若共同前綴完全相同，則較長字串被視為較大；或兩者同長且完全相同則回傳 0。
    c1 = ord(str1[index]) if index < len(str1) else 0
    c2 = ord(str2[index]) if index < len(str2) else 0
    return c1 - c2
