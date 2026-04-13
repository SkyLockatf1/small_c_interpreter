import lexer
import parser
import interpreter
codes: list = []
if __name__ == "__main__":
    interpreter_instance = interpreter.interpreter()
    trace_enabled = False
    while True:
            code = input("sc> ")
            #interactive command line
            if code.lower() == "exit":
                break
            code = code.strip()#remove leading and trailing spaces
            print(f"Input code: {code}")
            codes.append(code)
            try:
                lexer_instance = lexer.lexer(code)
                tokens = lexer_instance.tokenize()
                parser_instance = parser.parser(tokens)
            except Exception as e:#catch any exception and print it
                print(e)
            # print("Tokens:")