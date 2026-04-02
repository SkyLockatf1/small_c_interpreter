import enum

class token_type(enum.Enum):
    keyword = 1
    number = 2
    hexadecimal = 3
    string = 4
    char=5
    identifier = 6
    operator = 7
    punctuator = 8
    
class token:
    def __init__(self, type: token_type,line: int, value: str):
        self.type: token_type = type
        self.line: int = line
        self.value: str = value
keywords = ["int","char","void","if","else","while","for","return","do","continue","break"]
oprators = ["!","~","+", "-", "*", "/", "%", "<", ">", "=", "&", "^", "|"]
oprators_2 = ["++","--","==","!=","<=",">=","&&","||","<<",">>","+=","-=","*=","/=","%="]
punctuator= [";","(",")","{","}","[","]",",",".","?",":"]
class lexer:
    def __init__(self,codes: str):
        self.codes: str = codes
        self.position: int = 0
        self.line: int = 1
        self.tokens: list[token] = []
    def tokenize(self):
        while self.position < len(self.codes):
            cur_token = self.codes[self.position]
            #skip spaces/line breaks/tabs
            if (cur_token.isspace() or cur_token == '\n' or cur_token == '\t'):
                if cur_token == '\n':
                    self.line += 1
                self.position+=1
            #comment
            elif(self.position+1 < len(self.codes) and self.codes[self.position:self.position+2] in ['/*','//']):
                #single line comment
                if(self.codes[self.position:self.position+2]=='//'):
                    while (self.position < len(self.codes) and self.codes[self.position] != '\n'):
                        self.position+=1
                #multi line comment
                else:
                    while (self.position+1 < len(self.codes) and self.codes[self.position:self.position+2] != '*/'):
                        if(self.codes[self.position] == '\n'):
                            self.line += 1
                        self.position+=1
                    if(self.position+1 >= len(self.codes)):
                        raise Exception(f"Unterminated multi-line comment at line {self.line}")
                    self.position+=2#skip the closing */
            elif(cur_token == '#'):
                pass
                self.position+=8#skip #define
                macro_name: str = ""
                macro_value: int = 0
            elif(cur_token in oprators):
                oprator = cur_token
                self.position+=1
                if (self.position < len(self.codes) and self.codes[self.position-1:self.position+1] in oprators_2):
                    oprator += self.codes[self.position]
                    self.position+=1
                self.tokens.append(token(token_type.operator,self.line,oprator))
            #keyword int,char,void,if,else,else,while,for,return
            elif(cur_token.isalpha() or cur_token=="_"):
                ident=cur_token
                self.position+=1
                while (self.position < len(self.codes) and (self.codes[self.position].isalpha() or self.codes[self.position].isdigit() or self.codes[self.position]=="_")):
                    cur_token = self.codes[self.position]
                    ident += cur_token
                    self.position+=1
                if(ident in keywords):
                    self.tokens.append(token(token_type.keyword,self.line,ident))
                else:
                    self.tokens.append(token(token_type.identifier,self.line,ident))
            #number or hexadecimal
            elif(cur_token.isdigit()):
                num=cur_token
                self.position+=1
                # Check for hexadecimal (0x prefix)
                if(cur_token == '0' and self.position < len(self.codes) and self.codes[self.position].lower() == 'x'):
                    cur_token = self.codes[self.position]
                    num += cur_token
                    self.position+=1
                    if(self.position >= len(self.codes) or not self.codes[self.position].lower() in "0123456789abcdef"):
                        raise Exception(f"Syntax error: Invalid hexadecimal number: missing digits after 0x at line {self.line}")
                    while (self.position < len(self.codes) and self.codes[self.position].lower() in "0123456789abcdef"):
                        cur_token = self.codes[self.position]
                        num += cur_token
                        self.position+=1
                    self.tokens.append(token(token_type.hexadecimal, self.line, num))
                else:
                    # Decimal number
                    while (self.position < len(self.codes) and self.codes[self.position].isdigit()):
                        cur_token = self.codes[self.position]
                        num += cur_token
                        self.position+=1
                    self.tokens.append(token(token_type.number, self.line, num))
            #string/character literal
            elif(cur_token == '"' or cur_token == "'"):
                quote_type = cur_token
                string = ""
                self.position+=1
                while(self.position < len(self.codes) and self.codes[self.position] != quote_type):
                    #eacape sequence
                    if(self.codes[self.position]=='\\'):
                        if(self.position+1 >= len(self.codes)):
                            if(quote_type == '"'):
                                raise Exception(f"Syntax error: Unterminated string literal at line {self.line}")
                            else:
                                raise Exception(f"Syntax error: Unterminated character literal at line {self.line}")
                        else:
                            self.position+=1
                        if(self.codes[self.position]=='n'):
                            string += '\n'
                        elif(self.codes[self.position]=='t'):
                            string += '\t'
                        elif(self.codes[self.position]=='0'):
                            string += '\0'
                        elif(self.codes[self.position]=='\\'):
                            string += '\\'
                        elif(self.codes[self.position]=='"'):
                            string += '"'
                        elif(self.codes[self.position]=="'"):
                            string += "'"
                        else:
                            raise Exception(f"Syntax error: Invalid escape sequence: \\{self.codes[self.position]} at line {self.line}")
                    else:
                        string += self.codes[self.position]
                    self.position+=1
                if(self.position >= len(self.codes)):
                    if(quote_type == '"'):
                        raise Exception(f"Syntax error: Unterminated string literal at line {self.line}")
                    else:
                        raise Exception(f"Syntax error: Unterminated character literal at line {self.line}")
                self.position+=1#skip the closing quote
                if(quote_type == "'" and len(string) != 1):
                    raise Exception(f"Syntax error: Invalid character literal at line {self.line}: character literal must be a single character")
                if(quote_type == '"'):
                    self.tokens.append(token(token_type.string, self.line, string))
                else:
                    self.tokens.append(token(token_type.char, self.line, string))
            # punctuator
            elif (cur_token in punctuator):
                self.position+=1
                self.tokens.append(token(token_type.punctuator, self.line, cur_token))
            # unexpected character
            else:
                raise Exception(f"Syntax error: Unexpected character: {cur_token}")
        return self.tokens
                