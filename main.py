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

def analyze_program(source: str, macro_definitions: dict[str, str], line_start: int = 1) -> list:
    """執行共用的 lexer/parser 分析流程，回傳最外層 AST 節點。"""
    lexer_instance = lexer.lexer(source, macro_definitions, line_start=line_start)
    tokens = lexer_instance.tokenize()
    parser_instance = parser.parser(tokens)
    return parser_instance.parse()

def program_has_main(program: list) -> bool:
    """檢查完整程式 AST 是否定義了 main()。"""
    return any(isinstance(ast, parser.FunctionDef) and ast.name == "main" for ast in program)

def load_program_declarations(runtime: interpreter.Interpreter, program: list) -> None:
    """只載入完整程式的函式定義與全域宣告，不執行 top-level 裸露語句。"""
    for ast in program:
        if isinstance(ast, parser.FunctionDef):
            runtime.evaluate(ast)
    for ast in program:
        if isinstance(ast, parser.VarDecl):
            runtime.evaluate(ast)

def run_program_buffer(buffer: list[str], macro_definitions: dict[str, str], trace_enabled: bool) -> interpreter.Interpreter | None:
    """使用全新的 runtime，從 main() 執行目前的程式緩衝區。"""
    if not buffer:
        print("Error: no program to run.")
        return None

    source = "\n".join(buffer) + "\n"
    program = analyze_program(source, dict(macro_definitions))
    if not program_has_main(program):
        print("Error: main function not found.")
        return None

    runtime = interpreter.Interpreter()
    # 函式定義與全域宣告只是 RUN 前的載入流程，不屬於 main() 的逐步執行 trace。
    load_program_declarations(runtime, program)

    main_call = parser.CallExpr(parser.Identifier("main", 0), [], 0)
    # TRACE 需要保留 buffer 原始行文字，才能用 AST line number 找回使用者輸入的語句。
    runtime.trace_source_lines = {line_number: line for line_number, line in enumerate(buffer, start=1)}
    runtime.trace_enabled = trace_enabled
    try:
        try:
            return_value = runtime.evaluate(main_call)
        except interpreter.ExitSignal as signal:
            return_value = signal.code
    finally:
        runtime.trace_source_lines = {}
    if return_value is None:
        return_value = 0
    print(f"Program exited with return value {return_value}.")
    return runtime

def check_program_buffer(buffer: list[str], macro_definitions: dict[str, str]) -> None:
    """只檢查目前程式緩衝區的 lexer/parser 錯誤，不執行程式。"""
    if not buffer:
        print("Error: no program to check.")
        return

    source = "\n".join(buffer) + "\n"
    program = analyze_program(source, dict(macro_definitions))
    interpreter.check_semantics(program)
    print("No errors found.")
 
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
    print("""======================================
Small-C Interactive Interpreter v3.0
System Software Final Project , Spring 2026
======================================""")
    buffer = []       # 程式碼緩衝區，儲存所有已輸入的 Small-C 程式行
    is_dirty = False  # 追蹤緩衝區是否有未儲存的修改
    # ... 初始化你的實例 ...
    interpreter_instance = interpreter.Interpreter()
    macro_definitions: dict[str, str] = {} # 儲存巨集定義的字典，key 是巨集名稱，value 是巨集展開後的內容
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
                # 若有未儲存修改，離開前先詢問使用者確認
                if is_dirty:
                    confirm = input(
                        "Buffer has unsaved changes. Quit anyway? [y/N]: "
                    ).strip().lower()
                    if confirm != "y":
                        print("Quit cancelled.")
                        continue
                break
            elif cmd == "CLEAR":
                repl.CLEAR()
            elif cmd == "ABOUT":
                repl.ABOUT()
            elif cmd == "HELP":
                repl.HELP(args)
            elif cmd == "LIST":
                handle_list(buffer, args)
            elif cmd == "DELETE":
                handle_delete(buffer, args)
                is_dirty = True  # 刪除後標記為已修改
            elif cmd == "INSERT":
                # INSERT 回傳 True 才代表有實際插入內容
                if handle_insert(buffer, args):
                    is_dirty = True
            elif cmd == "EDIT":
                m_single = re.fullmatch(RE_SINGLE, args)
                if m_single:
                    n = int(m_single.group(1))
                    # EDIT 回傳 True 才代表使用者有實際更改內容
                    if repl.EDIT(buffer, n):
                        is_dirty = True
                else:
                    raise Exception(f"Runtime error: Invalid format '{args}'. Use 'n' for editing a specific line.")
            elif cmd == "APPEND":
                # APPEND 回傳 True 才代表有實際追加內容
                if repl.APPEND(buffer):
                    is_dirty = True
            elif cmd == "RUN":
                trace_enabled = interpreter_instance.trace_enabled
                next_interpreter = run_program_buffer(buffer, macro_definitions, trace_enabled)
                if next_interpreter is not None:
                    interpreter_instance = next_interpreter
            elif cmd == "CHECK":
                check_program_buffer(buffer, macro_definitions)
            elif cmd == "NEW":
                # 若有未儲存修改，先詢問使用者是否確認放棄
                if is_dirty:
                    confirm = input(
                        "Buffer has unsaved changes. Discard all and start fresh? [y/N]: "
                    ).strip().lower()
                    if confirm != "y":
                        print("NEW cancelled.")
                        continue
                buffer.clear()
                interpreter_instance = interpreter.Interpreter()
                macro_definitions.clear()
                is_dirty = False  # 清除後緩衝區乾淨
                print("All cleared.")
            elif cmd == "LOAD":
                if args:
                    # LOAD 成功後 is_dirty 重設為 False；使用者取消則維持原值
                    if repl.LOAD(buffer, args, is_dirty):
                        is_dirty = False
                else:
                    raise Exception("Runtime error: LOAD requires a filename. Usage: LOAD <filename>")
            elif cmd == "SAVE":
                if args:
                    repl.SAVE(buffer, args)
                    is_dirty = False  # 儲存成功後緩衝區乾淨
                else:
                    raise Exception(f"Runtime error: Invalid format '{args}'. Use 'filename' for saving the program.")
            elif cmd == "TRACE":
                if args:
                    if args.upper() == "ON":
                        interpreter_instance.trace_enabled = True
                        print("Trace mode enabled.")
                    elif args.upper() == "OFF":
                        interpreter_instance.trace_enabled = False
                        print("Trace mode disabled.")
                    else:
                        raise Exception(f"Runtime error: Invalid format '{args}'. Use 'ON' to enable or 'OFF' to disable tracing.")
                else:
                    raise Exception(f"Runtime error: Invalid format '{args}'. Use 'ON' to enable or 'OFF' to disable tracing.")
                pass
            elif cmd == "FUNCS":
                functions = list(interpreter_instance.symtable.iter_functions())
                for function in functions:
                    params = []
                    for param in function.params:
                        # 函式表保留原始陣列參數宣告，因此 FUNCS 顯示 int a[]，
                        # 實際呼叫時才在 interpreter 內退化成 int* / char*。
                        if param.is_array:
                            params.append(f"{param.var_type} {param.name}[]")
                        else:
                            params.append(f"{param.var_type} {param.name}")
                    print(f"{function.return_type} {function.name}({', '.join(params)}) line {function.line}")
                print("--- built-in functions ---")
                print("int putchar(int ch) [built-in]")
                print("int getchar() [built-in]")
                print("void printf(char *fmt, ...) [built-in]")
                print("void puts(char *s) [built-in]")
                print("int scanf(char *fmt, ...) [built-in]")
                print("int strlen(char *s) [built-in]")
                print("void strcpy(char *dest, char *src) [built-in]")
                print("int strcmp(char *s1, char *s2) [built-in]")
                print("void strcat(char *dest, char *src) [built-in]")
                print("int abs(int x) [built-in]")
                print("int max(int a, int b) [built-in]")
                print("int min(int a, int b) [built-in]")
                print("int pow(int base, int exp) [built-in]")
                print("int sqrt(int x) [built-in]")
                print("int mod(int a, int b) [built-in]")
                print("int rand() [built-in]")
                print("void srand(int seed) [built-in]")
                print("void memset(char *ptr, int val, int n) [built-in]")
                print("int sizeof_int() [built-in]")
                print("int sizeof_char() [built-in]")
                print("int atoi(char *s) [built-in]")
                print("void itoa(int val, char *str) [built-in]")
                print("void exit(int code) [built-in]")
            elif cmd == "VARS":
                # VARS 只顯示目前全域變數；函式呼叫期間的區域變數不列入驗收輸出。
                variables = list(interpreter_instance.symtable.iter_vars())
                vm = interpreter_instance.memory
                if not variables:
                    print("No variables defined.")
                else:
                    for symbol in variables:
                        name = symbol.name
                        var_type = symbol.var_type
                        addr = symbol.addr
                        if symbol.is_array:
                            # 陣列需顯示長度與前十個元素；超過十個元素用 ... 省略。
                            values = []
                            shown_count = min(symbol.array_length, 10)
                            for index in range(shown_count):
                                value = vm.array_read(addr, index, var_type)
                                # char 陣列同時顯示數值與可讀字元，方便檢查字串內容與 \0。
                                if var_type == 'char' and value == 0:
                                    values.append("0 ('\\0')")
                                elif var_type == 'char' and value == 10:
                                    values.append("10 ('\\n')")
                                elif var_type == 'char' and value == 9:
                                    values.append("9 ('\\t')")
                                elif var_type == 'char' and 32 <= value <= 126:
                                    values.append(f"{value} ('{chr(value)}')")
                                else:
                                    values.append(str(value))
                            if symbol.array_length > 10:
                                values.append("...")
                            print(f"{var_type} {name}[{symbol.array_length}] = {{{', '.join(values)}}}")
                        elif var_type == 'int':
                            val = vm.get_int(addr)
                            print(f"int {name} = {val}")
                        elif var_type == 'char':
                            # char 以整數值為主，若是常見可顯示字元則附上字元形式。
                            val = vm.get_char(addr)
                            if val == 0:
                                print(f"char {name} = {val} ('\\0')")
                            elif val == 10:
                                print(f"char {name} = {val} ('\\n')")
                            elif val == 9:
                                print(f"char {name} = {val} ('\\t')")
                            elif 32 <= val <= 126:
                                print(f"char {name} = {val} ('{chr(val)}')")
                            else:
                                print(f"char {name} = {val}")
                        elif var_type == 'int*' or var_type == 'char*':
                            # 指標變數的目前值就是其指向位址；0 視為 NULL。
                            ptr = vm.get_ptr(addr)
                            ptr_text = "NULL" if ptr == 0 else f"0x{ptr:04x}"
                            print(f"{var_type} {name} = {ptr_text}")
                        else:
                            print(f"{var_type} {name} = <unsupported>")
            
            
            # 2. 如果不是環境指令，才視為 Small-C 程式碼執行
            else:
                line_start = len(buffer) + 1  # 本次輸入在 buffer 的起始行號
                pending_buffer = raw_input + "\n" # 先把第一行程式碼存進 buffer，後續如果不完整再繼續讀取
                buffer.append(raw_input) # 只有程式碼才存進 buffer (依規範而定)
                is_dirty = True  # 輸入程式碼後標記為已修改
                while not check_input_complete(pending_buffer):
                    next_line = input(">>> ").strip()
                    pending_buffer += next_line + "\n"
                    buffer.append(next_line)
                # 執行 Lexer, Parser...
                program = analyze_program(pending_buffer, macro_definitions, line_start=line_start)
                for ast in program:
                    result = interpreter_instance.evaluate(ast)

        except interpreter.ExitSignal as signal:
            print(f"Program exited with return value {signal.code}.")
        except Exception as e:
            print(e)
