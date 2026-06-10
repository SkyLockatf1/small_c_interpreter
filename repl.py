import os

# 顯示系統/專案說明（待實作）
def ABOUT():
    # 保留原本酷酷的 ASCII Art 視覺
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
║  >> [Project] Small-C Interactive Interpreter v3.0                           ║
║  >> [Semester] System Software, Spring 2026                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    # 印出作者資訊
    print("--- 專題基本資訊 ---")
    print("解譯器名稱: Small-C Interactive Interpreter")
    print("版本號碼  : v3.0")
    print("作者資訊  : [羅敬軒 B1329030]")
    print("作者資訊  : [陳立峰 B1329054]")
    print("作者資訊  : [黃立昕 B1329020]")
    print("修課學期  : 114學年度第二學期 (Spring 2026)")
    print("========================================================================")

# 顯示指定指令的說明
def HELP(cmd: str = ""):
    # 轉換成無空格的大寫字串，以支援作業要求的不區分大小寫 (case-insensitive)
    cmd = cmd.strip().upper() if cmd else ""
    
    if not cmd:
        # 3.1 規範：當使用者單獨輸入 HELP 時，顯示所有環境指令的摘要說明
        print("\n==================== Small-C 環境指令摘要 ====================")
        print("【程式管理指令】")
        print("  LOAD <filename>     : 從檔案載入 Small-C 原始碼至緩衝區")
        print("  SAVE <filename>     : 將目前程式緩衝區內容儲存至檔案")
        print("  LIST                : 列出緩衝區完整內容 (可加行號或範圍，如 LIST 1-5)")
        print("  EDIT <n>            : 修改第 n 行的程式碼")
        print("  DELETE <n>          : 刪除第 n 行程式碼 (可指定範圍，如 DELETE 1-5)")
        print("  INSERT <n>          : 在第 n 行之前進入多行插入模式")
        print("  APPEND              : 在緩衝區末尾進入多行追加模式")
        print("  NEW                 : 清除緩衝區內容並重置所有全域變數與狀態")
        print("\n【執行與除錯指令】")
        print("  RUN                 : 執行目前緩衝區程式 (從 main 函式開始)")
        print("  CHECK               : 進行語法與語意檢查而不實際執行")
        print("  TRACE ON / OFF      : 開啟或關閉逐行語句執行追蹤模式")
        print("  VARS                : 顯示目前所有全域變數的名稱、型別與當前值")
        print("  FUNCS               : 列出所有自訂與內建函式的資訊")
        print("\n【系統指令】")
        print("  HELP [command]      : 顯示指令摘要，或指定特定指令的詳細說明")
        print("  ABOUT               : 顯示解譯器的軟體版本、作者與修課資訊")
        print("  CLEAR               : 清除終端機畫面")
        print("  QUIT / EXIT         : 關閉並結束解譯器環境")
        print("========================================================================")
        print("提示：輸入 'HELP <指令名稱>' 可查看該指令的詳細用法與範例（例：HELP LIST）。\n")
    else:
        # 3.1 規範：當輸入 HELP <command> 時，顯示該指令的詳細說明與使用範例
        print(f"\n--- 指令詳細說明: {cmd} ---")
        
        # 程式管理類
        if cmd == "LOAD":
            print("用法: LOAD <filename>")
            print("說明: 讀取指定的 Small-C 原始碼檔案並載入程式緩衝區。會覆蓋目前的緩衝區。")
        elif cmd == "SAVE":
            print("用法: SAVE <filename>")
            print("說明: 將目前程式緩衝區的所有程式碼，寫入指定的檔案中。")
        elif cmd == "LIST":
            print("用法: LIST 或 LIST <n> 或 LIST <n1>-<n2>")
            print("範例: LIST 5 (看第五行) | LIST 1-10 (看第一到十行)")
            print("說明: 顯示程式緩衝區的原始碼，每行前方會標示行號。")
        elif cmd == "EDIT":
            print("用法: EDIT <n>")
            print("說明: 顯示第 n 行內容並允許直接輸入新程式碼取代。若直接按 Enter 則取消修改。")
        elif cmd == "DELETE":
            print("用法: DELETE <n> 或 DELETE <n1>-<n2>")
            print("說明: 刪除指定行號或範圍內的程式碼，其後的行號會自動遞減前移。")
        elif cmd == "INSERT":
            print("用法: INSERT <n>")
            print("說明: 在第 n 行程式碼之前插入新程式碼，輸入單獨一行的 '.' 可退出該模式。")
        elif cmd == "APPEND":
            print("用法: APPEND")
            print("說明: 在目前程式碼的最末端進入多行追加模式，直到輸入單獨一行的 '.' 為止。")
        elif cmd == "NEW":
            print("用法: NEW")
            print("說明: 完全清空程式緩衝區，並將解譯器的全域變數、函式定義與執行狀態重置。")
            
        # 執行除錯類
        elif cmd == "RUN":
            print("用法: RUN")
            print("說明: 開始對緩衝區程式碼進行編譯解析，若無語法錯誤則從 main() 開始執行。")
        elif cmd == "CHECK":
            print("用法: CHECK")
            print("說明: 對緩衝區程式碼進行語法與語意檢查。若無錯誤會顯示 'No errors found'。")
        elif cmd == "TRACE":
            print("用法: TRACE ON 或 TRACE OFF")
            print("說明: 開啟追蹤模式後，RUN 執行時會在每個語句執行前印出 [Line n <statement>]。")
        elif cmd == "VARS":
            print("用法: VARS")
            print("說明: 印出當前全域符號表內所有變數的名稱、型別與當前數值（包含陣列與指標）。")
        elif cmd == "FUNCS":
            print("用法: FUNCS")
            print("說明: 印出所有已登記的函式（包含使用者自訂與 [built-in] 內建函式）的宣告規格。")
            
        # 系統指令類
        elif cmd == "ABOUT":
            print("用法: ABOUT")
            print("說明: 顯示此 Small-C 互動式解譯器的版本版權資訊以及開發團隊名單。")
        elif cmd == "CLEAR":
            print("用法: CLEAR")
            print("說明: 清除目前終端機螢幕的所有雜亂輸出，恢復乾淨的命令提示列。")
        elif cmd in ["QUIT", "EXIT"]:
            print("用法: QUIT 或 EXIT")
            print("說明: 安全退出 Small-C 互動式解譯器。")
        else:
            print(f"錯誤: 找不到環境指令 '{cmd}'。請確認拼字是否正確。")
        print("========================================================================")

# 進入多行追加模式，輸入單獨 "." 結束
# 回傳 True 表示有實際追加內容，False 表示使用者立即輸入 "." 而未修改 buffer
def APPEND(buffer:list[str]) -> bool:
    modified = False
    while True:
        # 不使用 strip()，避免把使用者輸入的程式縮排移除。
        new_code = input("Enter code to append (or '.' to finish): ")
        if new_code.strip() == ".": # 空行結束輸入
            break
        buffer.append(new_code)
        modified = True  # 至少追加了一行才標記為已修改
    return modified

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
# 回傳 True 表示有實際更改內容，False 表示使用者按 Enter 取消而未修改 buffer
def EDIT(buffer: list[str], arg: int) -> bool:
    if len(buffer) == 0:
        raise Exception("REPL error: Program buffer is empty.")
    if arg < 1 or arg > len(buffer):
        raise Exception(f"REPL error: Index {arg} out of bounds. Valid range is 1 to {len(buffer)}")
    print(f"Current code at line {arg}: {buffer[arg-1]}")
    # 空字串才代表取消；若使用者輸入前導空白，必須保留作為程式縮排。
    new_code = input("Enter new code: ")
    if new_code.strip() == "":
        return False  # 使用者直接按 Enter 取消，未修改 buffer
    buffer[arg-1] = new_code
    return True  # 實際更改了內容

# 在第 arg 行之前插入；arg=len(buffer)+1 代表尾端插入
# 回傳 True 表示有實際插入內容，False 表示使用者立即輸入 "." 而未修改 buffer
def INSERT(buffer: list[str], arg: int) -> bool:
    if arg < 1 or arg > len(buffer)+1:
        raise Exception(f"REPL error: Index {arg} out of bounds. Valid range is 1 to {len(buffer)+1}")
    offset = 0
    while True:
        insert_code = input("Enter code to insert (or '.' to finish):").strip()
        if insert_code == ".":  # 空行結束輸入
            break
        # 使用 offset 保留多行插入的原始順序
        buffer.insert(arg-1+offset, insert_code)
        offset += 1
    return offset > 0  # offset > 0 表示至少插入了一行

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
def LOAD(buffer: list[str], filename: str, is_dirty: bool) -> bool:
    """
    從指定檔案載入 Small-C 原始碼至程式緩衝區。
    
    - 若緩衝區有未儲存修改（is_dirty=True），先詢問使用者是否放棄。
    - 載入成功後顯示讀取行數，並回傳 True；取消或失敗則回傳 False。
    """
    if filename.strip() == "":
        raise Exception("REPL error: LOAD requires a filename.")

    # 若緩衝區有未儲存的修改，提示使用者確認後再覆蓋
    if is_dirty:
        confirm = input(
            f"Buffer has unsaved changes. Discard and load '{filename}'? [y/N]: "
        ).strip().lower()
        if confirm != "y":
            print("Load cancelled.")
            return False  # 使用者選擇不放棄，載入取消

    try:
        with open(filename, "r", encoding="utf-8") as file:
            lines = file.read().splitlines()  # 讀取所有行，保留空行，去除換行符號
        # 清除現有緩衝區並載入新內容
        buffer.clear()
        buffer.extend(lines)
        print(f"Loaded {len(buffer)} lines from '{filename}'.")
        return True  # 載入成功
    except FileNotFoundError:
        raise Exception(f"REPL error: File '{filename}' not found.")
    except PermissionError:
        raise Exception(f"REPL error: Permission denied when reading '{filename}'.")
    except UnicodeDecodeError:
        raise Exception(
            f"REPL error: '{filename}' is not valid UTF-8. "
            "Please save the file as UTF-8 encoding and try again."
        )
    except OSError as error:
        raise Exception(f"REPL error: Could not read '{filename}': {error}")

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
