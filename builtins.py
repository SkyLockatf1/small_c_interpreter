import math
import random
from memory import VirtualMemory

vm = VirtualMemory()

# void puts(char* str);
def puts(char_ptr: str)-> None:
    print(char_ptr)

# void printf(char* fmt, ...);
def printf(format_str, *args)-> None:
    # 簡化版 printf，會檢查格式碼與參數型別是否一致。
    result = ""
    arg_index = 0
    i = 0
    while i < len(format_str):
        if format_str[i] == '%' and i + 1 < len(format_str):
            specifier = format_str[i + 1]
            if specifier == '%':
                result += '%'
                i += 2
            elif specifier == 'd':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not int:
                    raise Exception(f"Runtime error: printf expects int for %d, got {type(args[arg_index]).__name__}")
                result += str(args[arg_index])
                arg_index += 1
                i += 2
            elif specifier == 's':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not str:
                    raise Exception(f"Runtime error: printf expects str for %s, got {type(args[arg_index]).__name__}")
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
                    raise Exception(f"Runtime error: printf expects char for %c, got {type(value).__name__}")
                arg_index += 1
                i += 2
            elif specifier == 'x':
                if arg_index >= len(args):
                    raise Exception("Runtime error: printf argument missing")
                if type(args[arg_index]) is not int:
                    raise Exception(f"Runtime error: printf expects int for %x, got {type(args[arg_index]).__name__}")
                result += format(args[arg_index], 'x')
                arg_index += 1
                i += 2
            else:
                result += format_str[i]
                i += 1
        else:
            result += format_str[i]
            i += 1
    if arg_index != len(args):
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
    random.seed(seed)

def rand()-> int:
    return random.randint(0, 32767)

#memory and tool functions
def memoset(char_ptr: int, value: int, num: int)-> None:
    for i in range(num):
        vm.set_char(char_ptr + i, value)
#int strlen(char* str);
def strlen(str_addr: int)-> int:
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
def strcpy(dest_addr: int, src_addr: int)-> None:

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
def strcmp(s1_addr: int, s2_addr: int)-> int:
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