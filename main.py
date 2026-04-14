import re
import lexer
import parser
import interpreter
import repl

# List用
RE_SINGLE = r'^(\d+)$'
RE_RANGE = r'^(\d+)-(\d+)$'

def handle_list(args, codes):

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
        raise Exception(f"Runtime error: Invalid format '{args}'. Use 'n' or 'n1-n2'.")
    repl.LIST(n, codes)

if __name__ == "__main__":
    codes = []  # 原本的 program buffer
    # ... 初始化你的實例 ...

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
            elif cmd == "LIST":
                handle_list(args, codes)
            elif cmd == "APPEND":
                # 進入多行輸入模式 (你之後要實作的部分)
                pass
            
            
            # 2. 如果不是環境指令，才視為 Small-C 程式碼執行
            else:
                codes.append(raw_input) # 只有程式碼才存進 buffer (依規範而定)
                # 執行 Lexer, Parser...
                lexer_instance = lexer.lexer(raw_input)
                tokens = lexer_instance.tokenize()
                # ... 
                
        except Exception as e:
            print(e)