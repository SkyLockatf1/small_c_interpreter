import math
import random
from memory import VirtualMemory

# void puts(char* str);

def puts(char_ptr: str)-> None:
    print(char_ptr)

# void printf(char* fmt, ...);
def printf(format_str, *args)-> None:
    # 簡化版 printf：支援 %%、%d、%s、%c、%x，並檢查參數數量與型別。
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
                elif type(args[arg_index]) is str and len(args[arg_index]) == 1: # 允許 char 以 int 形式輸出
                    # char 在此直譯器中可能以長度為 1 的字串表示。
                    result += str(ord(args[arg_index]))
                else:
                    if(type(args[arg_index]).__name__=='str'):
                        raise Exception("Runtime error: printf expects int or hex for %d, got char*")
                    else:
                        raise Exception(f"Runtime error: printf expects int or hex for %d, got {type(args[arg_index]).__name__}")
                arg_index += 1
                i += 2
            elif specifier == 's':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not str:
                    raise Exception(f"Runtime error: printf expects char* for %s, got {type(args[arg_index]).__name__}")
                result += args[arg_index]
                arg_index += 1
                i += 2
            elif specifier == 'c':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                value = args[arg_index]
                if type(value) is int:
                    result += chr(value)
                elif type(value) is str and len(value) == 1:
                    result += value
                else:
                    if(type(args[arg_index]).__name__=='str'):
                        raise Exception("Runtime error: printf expects char for %d, got char*")
                    else:
                        raise Exception(f"Runtime error: printf expects char for %c, got {type(value).__name__}")
                arg_index += 1
                i += 2
            elif specifier == 'x':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not int:
                    if(type(args[arg_index]).__name__=='str'):
                        raise Exception("Runtime error: printf expects char for %d, got char*")
                    else:
                        raise Exception(f"Runtime error: printf expects int or hex for %x, got {type(args[arg_index]).__name__}")
                result += hex(args[arg_index]) # hex() 會回傳字串
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

#int putchar(int ch);
def putchar(ch:int)-> int:
    print(chr(ch), end='')
    return ch

def getchar()-> int:
    ch = input()
    return ord(ch[0]) if ch else -1

#math functions
def abs(x:int)-> int:
    return x if x >= 0 else -x

def max(a:int, b:int)-> int:
    return a if a >= b else b

def min(a:int, b:int)-> int:
    return a if a <= b else b

def pow(base:int, exp:int)-> int:
    return base ** exp if exp >= 0 else 0

def sqrt(x:int)-> int:
    if(x < 0):
        raise Exception("Runtime error: sqrt argument must be a non-negative integer")
    return math.floor(x**0.5)

def mod(a:int, b:int)-> int:
    if(b == 0):
        raise Exception("Runtime error: division by zero")
    return a % b

def srand(seed:int)-> None:
    random.seed(seed) #處理種子傳遞問題

def rand()-> int:
    return random.randint(0, 32767)

#memory and tool functions
def memset(vm: VirtualMemory,char_ptr: int, value: int, num: int)-> None:
    for i in range(num):
        vm.set_char(char_ptr + i, value)
#int strlen(char* str);
def strlen(vm: VirtualMemory,str_addr: int)-> int:
    length = 0
    while vm.get_char(str_addr + length) != 0:
        length += 1
    return length

def sizeof_int()-> int:
    return 4

def sizeof_char()-> int:
    return 1

def atio(char_str: str)-> int:
    return int(char_str)

#void strcpy(char *dest, char *src);
def strcpy(vm: VirtualMemory, dest_addr: int, src_addr: int)-> None:

    i = 0
    while True:
        vm.check_bounds(dest_addr, dest_addr + i, 1)
        vm.check_bounds(src_addr, src_addr + i, 1)

        c = vm.get_char(src_addr + i)
        vm.set_char(dest_addr + i, c)
        if c == 0:
            break
        i += 1

#int strcmp(char *s1, char *s2)
def strcmp(vm: VirtualMemory, s1_addr: int, s2_addr: int)-> int:
    vm.check_bounds(s1_addr, s1_addr + 1, 1)
    i = 0
    while True:
        c1 = vm.get_char(s1_addr + i)
        c2 = vm.get_char(s2_addr + i)
        if c1 != c2:
            return c1 - c2
        if c1 == 0: # both strings end
            return 0
        i += 1
