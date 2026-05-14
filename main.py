import re
import lexer
import parser
import interpreter
import repl

# List用
RE_SINGLE = r'^(\d+)$'
RE_RANGE = r'^(\d+)-(\d+)$'

def parse_line_args(args: str, command: str, allow_empty: bool, allow_range: bool) -> list[int]:
    # 根據 allow_empty 和 allow_range 來決定允許的參數格式，並在錯誤訊息中清楚說明。
    if allow_empty and allow_range:
        usage = "'n' or 'n1-n2' or without arguments"
    elif allow_range:
        usage = "'n' or 'n1-n2'"
    else:
        usage = "'n'"

    # 使用 fullmatch 進行嚴格檢查
    m_single = re.fullmatch(RE_SINGLE, args)
    m_range = re.fullmatch(RE_RANGE, args)

    if not args: #沒參數
        if allow_empty:
            return []
        raise Exception(f"Runtime error: Invalid format '{args}'. Use {usage} for {command}.")

    elif m_single:  #單參數
        n1 = int(m_single.group(1))
        return [n1]

    elif m_range and allow_range: #範圍參數
        n1, n2 = int(m_range.group(1)), int(m_range.group(2))
        return [n1, n2]

    # 只要不是允許的格式，就報錯（包含 1,5 或 1 5）
    raise Exception(f"Runtime error: Invalid format '{args}'. Use {usage} for {command}.")

def handle_list(buffer: list, args: str):
    n = parse_line_args(args, "LIST", allow_empty=True, allow_range=True)
    repl.LIST(buffer, n)

def handle_delete(buffer: list, args: str):
    n = parse_line_args(args, "DELETE", allow_empty=False, allow_range=True)
    repl.DELETE(buffer, n)

def handle_insert(buffer: list, args: str):
    n = parse_line_args(args, "INSERT", allow_empty=False, allow_range=False)
    repl.INSERT(buffer, n[0])
 
def check_input_complete(pending_buffer: str) -> bool:
    """只判斷 REPL 是否還需要續行；語法錯誤交給 lexer/parser 處理。"""
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    i = 0
    length = len(pending_buffer)
    state = "normal" # normal, block_comment, string_or_char （後者兩者都不處理括號配對）
    quote = None

    while i < length:
        ch = pending_buffer[i]

        if state == "block_comment":
            # 區塊註解未結束代表使用者可能還會繼續輸入下一行。
            if pending_buffer.startswith("*/", i):
                state = "normal"
                i += 2
                continue
            i += 1
            continue

        if state == "string_or_char":
            if ch == "\n":
                # 字串/字元是否允許跨行由 lexer 判斷；如果不允許跨行，這裡遇到換行就直接當作輸入結束，讓後續的 lexer 報錯。
                return True
            if ch == "\\":
                # 跳過跳脫字元後面的字元，避免把 \" 或 \' 誤判成字串結尾。
                i += 2
                continue
            if ch == quote:
                state = "normal"
                quote = None
            i += 1
            continue

        if ch == "\n":
            i += 1
            continue
        if pending_buffer.startswith("//", i):
            # 單行註解後面的括號不應影響完整性判斷。
            while i < length and pending_buffer[i] != "\n":
                i += 1
            continue
        if pending_buffer.startswith("/*", i):
            # 進入區塊註解後，只等待 */，不檢查其中的括號。
            state = "block_comment"
            i += 2
            continue
        if ch == '"' or ch == "'":
            # 字串/字元常數中的括號只是文字，不參與配對。
            state = "string_or_char"
            quote = ch
            i += 1
            continue
        if ch in "({[":
            stack.append(ch)
        elif ch in ")}]":
            # 多出的或錯配的右括號不是「未完成輸入」，交給 parser 報語法錯誤。
            if not stack or stack[-1] != pairs[ch]:
                return True
            stack.pop()
        i += 1

    if state == "block_comment" or stack:
        # 只有仍在區塊註解中，或仍有未關閉的左括號/大括號/中括號，才需要續行。
        return False
    return True

if __name__ == "__main__":
#     print(""" 
# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║                                                                              ║
# ║  ████████╗██████╗ ██╗██████╗ ██╗     ███████╗                                ║
# ║  ╚══██╔══╝██╔══██╗██║██╔══██╗██║     ██╔════╝                                ║
# ║     ██║   ██████╔╝██║██████╔╝██║     █████╗                                  ║
# ║     ██║   ██╔══██╗██║██╔═══╝ ██║     ██╔══╝                                  ║
# ║     ██║   ██║  ██║██║██║     ███████╗███████╗                                ║
# ║     ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝     ╚══════╝╚══════╝                                ║
# ║                                                         (                    ║
# ║  ███╗   ███╗███████╗ ██████╗  █████╗                     )                   ║
# ║  ████╗ ████║██╔════╝██╔════╝ ██╔══██╗                 _..-.._                ║
# ║  ██╔████╔██║█████╗  ██║  ███╗███████║               ,'       `.              ║
# ║  ██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║              |  ~~~~~~~  |             ║
# ║  ██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║               \         /              ║
# ║  ╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝                `-------'               ║
# ║                                                                              ║
# ║                                                                              ║
# ║  >> [XXXXXX]                                                                 ║
# ║  >> [XXXXXX]                                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
# """)
    buffer = []  # 原本的 program buffer
    # ... 初始化你的實例 ...
    interpreter_instance = interpreter.Interpreter()
    while True:
        try:
            raw_input = input("sc> ").strip()
            if not raw_input: continue
            
            # 分切指令與參數 (例如 "LIST 1-5" -> ["LIST", "1-5"])
            parts = raw_input.split(maxsplit=1)
            cmd = parts[0].upper()
            args = parts[1] if len(parts) > 1 else ""

            # 1. 處理環境指令
            if cmd == "EXIT" or cmd == "QUIT":
                break
            elif cmd == "CLEAR":
                repl.CLEAR()
            elif cmd == "ABOUT":
                repl.ABOUT()
            elif cmd == "HELP":
                repl.HELP()
            elif cmd == "LIST":
                handle_list(buffer, args)
            elif cmd == "DELETE":
                handle_delete(buffer, args)
            elif cmd == "INSERT":
                handle_insert(buffer, args)
            elif cmd == "EDIT":
                m_single = re.fullmatch(RE_SINGLE, args)
                if m_single:
                    n = int(m_single.group(1))
                    repl.EDIT(buffer, n)
                else:
                    raise Exception(f"Runtime error: Invalid format '{args}'. Use 'n' for editing a specific line.")
            elif cmd == "APPEND":
                repl.APPEND(buffer)
            elif cmd == "RUN":
                pass
            elif cmd == "NEW":
                buffer.clear()
                interpreter_instance = interpreter.Interpreter()
            elif cmd == "LOAD":
                pass
            elif cmd == "SAVE":
                if args:
                    repl.SAVE(buffer, args)
                else:
                    raise Exception(f"Runtime error: Invalid format '{args}'. Use 'filename' for saving the program.")
            elif cmd == "TRACE":
                pass
            elif cmd == "VARS":
                table = interpreter_instance.symtable.table
                if not table:
                    print("No variables defined.")
                else:
                    for name, info in table.items():
                        var_type = info['type']
                        addr = info['addr']
                        if var_type == 'int':
                            val = interpreter_instance.memory.get_int(addr)
                            print(f"int {name} = {val}")
                        elif var_type == 'char':
                            val = interpreter_instance.memory.get_char(addr)
                            # 仿照範例輸出： char ch = 65 ('A')
                            print(f"char {name} = {val} ('{chr(val)}')")
            
            
            # 2. 如果不是環境指令，才視為 Small-C 程式碼執行
            else:
                pending_buffer = raw_input + "\n" # 先把第一行程式碼存進 buffer，後續如果不完整再繼續讀取
                buffer.append(raw_input) # 只有程式碼才存進 buffer (依規範而定)
                while not check_input_complete(pending_buffer):
                    next_line = input(">>> ").strip()
                    pending_buffer += next_line + "\n"
                    buffer.append(next_line)
                # 執行 Lexer, Parser...
                lexer_instance = lexer.lexer(pending_buffer)
                tokens = lexer_instance.tokenize()
                parser_instance = parser.parser(tokens)
                program = parser_instance.parse()
                for ast in program:
                    print("AST:", ast)
                    result = interpreter_instance.evaluate(ast)
                # print("Result:", result)

        except Exception as e:
            print(e)
