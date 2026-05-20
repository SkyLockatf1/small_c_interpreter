import os

# 顯示系統/專案說明（待實作）
def ABOUT():
    print(""" 
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║  ████████╗██████╗ ██╗██████╗ ██╗     ███████╗                                ║
║  ╚══██╔══╝██╔══██╗██║██╔══██╗██║     ██╔════╝                                ║
║     ██║   ██████╔╝██║██████╔╝██║     █████╗                                  ║
║     ██║   ██╔══██╗██║██╔═══╝ ██║     ██╔══╝                                  ║
║     ██║   ██║  ██║██║██║     ███████╗███████╗                                ║
║     ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝     ╚══════╝╚══════╝                                ║
║                                                                              ║
║  ███╗   ███╗███████╗ ██████╗  █████╗                   (  )                  ║
║  ████╗ ████║██╔════╝██╔════╝ ██╔══██╗                 _..-.._                ║
║  ██╔████╔██║█████╗  ██║  ███╗███████║               ,'       `.              ║
║  ██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║              |  ~~~~~~~  |             ║
║  ██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║               \         /              ║
║  ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝                `-------'               ║
║                                                       ███████                ║
║                                                                              ║
║  >> [XXXXXX]                                                                 ║
║  >> [XXXXXX]                                                                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    pass

# 顯示指定指令的說明（待實作）
def HELP(cmd:str):
    pass

# 進入多行追加模式，輸入單獨 "." 結束
def APPEND(buffer:list[str]):
    while True:
        new_code = input("Enter code to append (or '.' to finish): ").strip()
        if new_code == ".": # 空行結束輸入
            break
        buffer.append(new_code)

# 依作業系統執行對應的清屏指令
def CLEAR() -> None:
    os.system("cls" if os.name == "nt" else "clear") #跨平台清屏

# 列出 buffer：支援全列、單行、範圍
def LIST(buffer:list[str], args:list[int]) -> None:
    if(len(buffer) == 0):
        raise Exception("REPL error: Program buffer is empty.")
    else:
        if len(args) == 0:
            for i in range(len(buffer)):
                print("["+str(i+1)+"]: "+buffer[i])
                
        elif len(args) == 1:
            if args[0] < 1 or args[0] > len(buffer):
                raise Exception(f"REPL error: Index {args[0]} out of bounds.")
            print("["+str(args[0])+"]: "+buffer[args[0]-1])

        elif len(args) == 2:
            # 範圍模式先檢查上下界，避免索引錯誤
            if args[0] < 1 or args[0] > len(buffer) or args[1] < 1 or args[1] > len(buffer):
                raise Exception(f"REPL error: Index out of bounds. Valid range is 1 to {len(buffer)}")
            if args[0] > args[1]: 
                raise Exception("REPL error: Start index cannot be greater than end index.")
            for i in range(args[0], args[1]+1):
                print("["+str(i)+"]: "+buffer[i-1])
        else:
            raise Exception(f"REPL error: Too many arguments for LIST. Expected 0, 1, or 2, got {len(args)}")

# 編輯指定行；輸入空字串代表取消修改
def EDIT(buffer: list[str], arg: int) -> None:
    if len(buffer) == 0:
        raise Exception("REPL error: Program buffer is empty.")
    else:
        if arg < 1 or arg > len(buffer):
            raise Exception(f"REPL error: Index {arg} out of bounds. Valid range is 1 to {len(buffer)}")
        print(f"Current code at line {arg}: {buffer[arg-1]}")
        new_code = input("Enter new code: ").strip()
        if new_code == "":
            return
        buffer[arg-1] = new_code

# 在第 arg 行之前插入；arg=len(buffer)+1 代表尾端插入
def INSERT(buffer: list[str], arg: int) -> None:
    if arg < 1 or arg > len(buffer)+1:
        raise Exception(f"REPL error: Index {arg} out of bounds. Valid range is 1 to {len(buffer)+1}")
    offset = 0
    while True:
        insert_code = input("Enter code to insert (or '.' to finish):").strip()
        if insert_code == ".":  # 空行結束輸入
            break
        # 使用 offset 保留多行插入的原始順序
        buffer.insert(arg-1+offset,insert_code)
        offset += 1

# 刪除單行或範圍；範圍刪除採反向避免索引位移
def DELETE(buffer: list[str], args: list[int]) -> None:
    if len(buffer) == 0:
        raise Exception("REPL error: Program buffer is empty.")
    else:
        if(len(args) == 0):
            raise Exception("REPL error: DELETE command requires at least one argument.")
        elif(len(args) == 1):
            if args[0] < 1 or args[0] > len(buffer):
                raise Exception(f"REPL error: Index {args[0]} out of bounds. Valid range is 1 to {len(buffer)}")
            buffer.pop(args[0]-1)
        elif(len(args) == 2):
            if args[0] < 1 or args[0] > len(buffer) or args[1] < 1 or args[1] > len(buffer):
                raise Exception(f"REPL error: Index out of bounds. Valid range is 1 to {len(buffer)}")
            if args[0] > args[1]:
                raise Exception("REPL error: Start index cannot be greater than end index.")
            for i in range(args[1], args[0]-1, -1):
                buffer.pop(i-1)
        else:
            raise Exception("REPL error: DELETE command requires 1 or 2 arguments.")
def SAVE(buffer: list[str], filename: str) -> None:
    if len(buffer) == 0:
        raise Exception("REPL error: Program buffer is empty.")
    if filename.strip() == "":
        raise Exception("REPL error: SAVE requires a filename.")

    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write("\n".join(buffer))
        print(f"Saved {len(buffer)} lines to '{filename}'.")
    except PermissionError:
        raise Exception(f"REPL error: Permission denied when trying to write to '{filename}'.")
    except IsADirectoryError:
        raise Exception(f"REPL error: Invalid filename '{filename}'.")
    except OSError as error:
        raise Exception(f"REPL error: Could not write to '{filename}': {error}")
