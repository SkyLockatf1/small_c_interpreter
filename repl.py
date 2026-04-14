import os

def ABOUT():
    pass
def HELP(cmd:str):
    pass
def APPEND(codes:list[str]):
    while True:
        new_code = input("Enter code to append (or '.' to finish): ").strip()
        if new_code == ".": # 空行結束輸入
            break
        codes.append(new_code)
def CLEAR():
    os.system("cls" if os.name == "nt" else "clear") #跨平台清屏
def LIST(args:list[int], buffer:list[str]):
    if(len(buffer) == 0):
        raise Exception("Runtime error: Program buffer is empty.")
    else:
        if len(args) == 0:
            for i in range(len(buffer)):
                print("["+str(i+1)+"]: "+buffer[i])
                
        elif len(args) == 1:
            if args[0] < 1 or args[0] > len(buffer):
                raise Exception(f"Runtime error: Index {args[0]} out of bounds.")
            print("["+str(args[0])+"]: "+buffer[args[0]-1])

        elif len(args) == 2:
            if args[0] < 1 or args[0] > len(buffer) or args[1] < 1 or args[1] > len(buffer):
                raise Exception(f"Runtime error: Index out of bounds. Valid range is 1 to {len(buffer)}")
            if args[0] > args[1]: 
                raise Exception("Runtime error: Start index cannot be greater than end index.")
            for i in range(args[0], args[1]+1):
                print("["+str(i)+"]: "+buffer[i-1])
        else:
            raise Exception(f"Runtime error: Too many arguments for LIST. Expected 0, 1, or 2, got {len(args)}")
def EDIT(codes: list[str], arg: int):
    if len(codes) == 0:
        raise Exception("Runtime error: Program buffer is empty.")
    else:
        if arg < 1 or arg > len(codes):
            raise Exception(f"Runtime error: Index {arg} out of bounds. Valid range is 1 to {len(codes)}")
        print(f"Current code at line {arg}: {codes[arg-1]}")
        new_code = input("Enter new code: ").strip()
        if new_code == "":
            return
        codes[arg-1] = new_code
def INSERT(codes: list[str], arg: int):
    if arg < 1 or arg > len(codes)+1:
        raise Exception(f"Runtime error: Index {arg} out of bounds. Valid range is 1 to {len(codes)+1}")
    offset = 0
    while True:
        insert_code = input("Enter code to insert (or '.' to finish):").strip()
        if insert_code == ".":  # 空行結束輸入
            break
        codes.insert(arg-1+offset,insert_code)
        offset += 1
def DELETE(codes: list[str], args: list[int]):
    if len(codes) == 0:
        raise Exception("Runtime error: Program buffer is empty.")
    else:
        if(len(args) == 0):
            raise Exception("Runtime error: DELETE command requires at least one argument.")
        elif(len(args) == 1):
            if args[0] < 1 or args[0] > len(codes):
                raise Exception(f"Runtime error: Index {args[0]} out of bounds. Valid range is 1 to {len(codes)}")
            codes.pop(args[0]-1)
        elif(len(args) == 2):
            if args[0] < 1 or args[0] > len(codes) or args[1] < 1 or args[1] > len(codes):
                raise Exception(f"Runtime error: Index out of bounds. Valid range is 1 to {len(codes)}")
            if args[0] > args[1]:
                raise Exception("Runtime error: Start index cannot be greater than end index.")
            for i in range(args[1], args[0]-1, -1):
                codes.pop(i-1)
        else:
            raise Exception("Runtime error: DELETE command requires 1 or 2 arguments.")