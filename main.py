import re
import lexer
import parser
import interpreter
import repl

# List用
RE_SINGLE = r'^(\d+)$'
RE_RANGE = r'^(\d+)-(\d+)$'

def handle_list(buffer: list, args: str):

    # 使用 fullmatch 進行嚴格檢查
    m_single = re.fullmatch(RE_SINGLE, args)
    m_range = re.fullmatch(RE_RANGE, args)

    if not args: #沒參數
        n = []

    elif m_single:  #單參數
        n1 = int(m_single.group(1))
        n = [n1]

    elif m_range: #範圍參數
        n1, n2 = int(m_range.group(1)), int(m_range.group(2))
        n = [n1, n2]
    else:
        # 只要不是以上兩種格式，就報錯（包含 1,5 或 1 5）
        raise Exception(f"Runtime error: Invalid format '{args}'. Use 'n' or 'n1-n2' or without arguments.")
    repl.LIST(buffer, n)
    
if __name__ == "__main__":
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
                pass
            elif cmd == "LOAD":
                pass
            elif cmd == "SAVE":
                pass
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
                buffer.append(raw_input) # 只有程式碼才存進 buffer (依規範而定)
                # 執行 Lexer, Parser...
                lexer_instance = lexer.lexer(raw_input)
                tokens = lexer_instance.tokenize()
                parser_instance = parser.parser(tokens)
                statements = parser_instance.parse()
                for ast in statements:
                    print("AST:", ast)
                    result = interpreter_instance.evaluate(ast)
                # print("Result:", result)

        except Exception as e:
            print(e)