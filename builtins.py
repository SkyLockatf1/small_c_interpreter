import math
from memory import VirtualMemory
from extra_c_type import char_ptr, int_ptr

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
            specifier_index = i + 1
            width_text = ""
            while specifier_index < len(format_str) and format_str[specifier_index].isdigit():
                width_text += format_str[specifier_index]
                specifier_index += 1
            if specifier_index >= len(format_str):
                raise Exception("Runtime error: printf format string ends after width")
            width = int(width_text) if width_text else 0
            specifier = format_str[specifier_index]
            if specifier == '%':
                if width_text:
                    raise Exception("Runtime error: printf width is not supported for %%")
                result += '%'
                i += 2
            elif specifier == 'd':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                value = args[arg_index]
                if type(value) is int:
                    result += str(value)
                elif type(value) is int_ptr:
                    result += str(value.addr)
                else:
                    got_type = type_mapping.get(type(value).__name__, type(value).__name__)
                    raise Exception(f"Runtime error: printf expects int for %d, got {got_type}")
                arg_index += 1
                i = specifier_index + 1
            elif specifier == 's':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not char_ptr:
                    got_type = type_mapping.get(type(args[arg_index]).__name__, type(args[arg_index]).__name__)
                    raise Exception(f"Runtime error: printf expects char* for %s, got {got_type}")
                # read_cstring 處理邊界驗證，不需要手動逐字元迴圈
                text = vm.read_cstring(args[arg_index].addr)
                result += text.rjust(width) if width else text
                arg_index += 1
                i = specifier_index + 1
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
                i = specifier_index + 1
            elif specifier == 'x':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not int:
                    got_type = type_mapping.get(type(args[arg_index]).__name__, type(args[arg_index]).__name__)
                    raise Exception(f"Runtime error: printf expects int for %x, got {got_type}")
                text = format(args[arg_index], 'x')
                result += text.rjust(width) if width else text
                arg_index += 1
                i = specifier_index + 1
            else:
                # 不支援的格式指定字照原字元輸出。
                raise Exception(f"Runtime error: printf unsupported format specifier %{width_text}{specifier}")
        else:
            result += format_str[i]
            i += 1
    if arg_index != len(args):
        # 格式字串解析完後仍有多餘參數，代表呼叫格式錯誤。
        raise Exception("Runtime error: printf argument count mismatch")
    print(result, end='')

# int scanf(char* fmt, ...);
def scanf(vm: VirtualMemory, fmt: char_ptr, *args) -> int:
    # scanf 的格式字串本身也存放在虛擬記憶體中，因此第一個參數必須是 char*。
    if type(fmt) is not char_ptr:
        got_type = type_mapping.get(type(fmt).__name__, type(fmt).__name__)
        raise Exception(f"Runtime error: scanf expects char* for format string, got {got_type}")

    format_str = vm.read_cstring(fmt.addr)
    specifiers = []
    i = 0
    # 第一輪只掃描格式字串，找出需要接收輸入的格式碼。
    # 本專案只支援 %d 與 %c；%C、%%、%s 等其他格式都視為程式錯誤。
    while i < len(format_str):
        if format_str[i] == '%':
            if i + 1 >= len(format_str):
                raise Exception("Runtime error: scanf format string ends with '%'")
            specifier = format_str[i + 1]
            if specifier not in ('d', 'c'):
                raise Exception(f"Runtime error: scanf unsupported format specifier %{specifier}")
            specifiers.append(specifier)
            i += 2
        else:
            i += 1

    if len(args) != len(specifiers):
        raise Exception("Runtime error: scanf argument count mismatch")

    # 先檢查所有指標型別與可寫入範圍；程式本身寫錯時不應消耗使用者輸入。
    # 型別錯誤不是「讀取失敗」，而是 runtime error，所以不會回傳成功讀取數量。
    for index, specifier in enumerate(specifiers):
        arg = args[index]
        if specifier == 'd':
            if type(arg) is not int_ptr:
                got_type = type_mapping.get(type(arg).__name__, type(arg).__name__)
                raise Exception(f"Runtime error: scanf expects int* for %d, got {got_type}")
            vm.check_ptr(arg.addr, 4)
        elif specifier == 'c':
            if type(arg) is not char_ptr:
                got_type = type_mapping.get(type(arg).__name__, type(arg).__name__)
                raise Exception(f"Runtime error: scanf expects char* for %c, got {got_type}")
            vm.check_ptr(arg.addr, 1)

    try:
        # 目前直譯器的輸入模型以一行為單位，與 getchar() 一樣使用 Python input()。
        input_text = input()
    except EOFError:
        return 0

    success_count = 0
    arg_index = 0
    input_index = 0
    i = 0
    while i < len(format_str):
        if format_str[i].isspace():
            # scanf 格式字串中的任意空白會吃掉輸入中的任意連續空白。
            while i < len(format_str) and format_str[i].isspace():
                i += 1
            while input_index < len(input_text) and input_text[input_index].isspace():
                input_index += 1
            continue

        if format_str[i] != '%':
            # 一般字元必須逐字匹配；不匹配屬於輸入格式不符，回傳已成功讀取的項目數。
            if input_index >= len(input_text) or input_text[input_index] != format_str[i]:
                return success_count
            input_index += 1
            i += 1
            continue

        specifier = format_str[i + 1]
        arg = args[arg_index]
        if specifier == 'd':
            # %d 讀取整數前會略過輸入空白，並接受可選的 + 或 - 號。
            while input_index < len(input_text) and input_text[input_index].isspace():
                input_index += 1

            number_start = input_index
            if input_index < len(input_text) and input_text[input_index] in '+-':
                input_index += 1

            digit_start = input_index
            while input_index < len(input_text) and input_text[input_index].isdigit():
                input_index += 1

            if digit_start == input_index:
                # 沒有讀到任何數字：輸入不匹配，不寫入目的變數。
                return success_count

            # 只有完整讀到一個整數後才寫入 int* 目標，避免失敗時污染原變數。
            vm.set_int(arg.addr, int(input_text[number_start:input_index]))
            success_count += 1
        elif specifier == 'c':
            # %c 直接讀下一個字元，不會自動略過空白；若要略過空白需在格式字串寫成 " %c"。
            if input_index >= len(input_text):
                return success_count
            ch = input_text[input_index]
            if ord(ch) > 127:
                raise Exception(f"Runtime error: scanf %c expects ASCII input, got {ord(ch)}")
            vm.set_char(arg.addr, ord(ch))
            input_index += 1
            success_count += 1

        arg_index += 1
        i += 2

    return success_count

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

# void strcat(char* dest, char* src);
def strcat(vm: VirtualMemory, dest: char_ptr, src: char_ptr) -> None:
    if type(dest) is not char_ptr:
        got_type = type_mapping.get(type(dest).__name__, type(dest).__name__)
        raise Exception(f"Runtime error: strcat expects char* for dest, got {got_type}")
    if type(src) is not char_ptr:
        got_type = type_mapping.get(type(src).__name__, type(src).__name__)
        raise Exception(f"Runtime error: strcat expects char* for src, got {got_type}")

    dest_text = vm.read_cstring(dest.addr)
    src_text = vm.read_cstring(src.addr)
    result = dest_text + src_text

    # dest 可能是 buf + n 這類中間指標，因此容量要從 dest.addr 算到 allocation 結尾。
    allocation = vm.find_allocation(dest.addr)
    if allocation is None:
        raise Exception(f"Runtime error: invalid memory access at {dest.addr:#x}")
    base, size = allocation
    remaining_size = base + size - dest.addr

    # write_cstring 會寫入 result 與結尾 \0，並在容量不足時回報 buffer overflow。
    vm.write_cstring(dest.addr, result, remaining_size)

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
