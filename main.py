import lexer
# import parser
import interpreter
codes: list = []
tokens: list[lexer.token] = []
parser = []
if __name__ == "__main__":
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
                del lexer_instance
                for token in tokens:
                    print(f"  {token.type}: {token.value}")
            except Exception as e:#catch any exception and print it
                print(e)
            print("Tokens:")