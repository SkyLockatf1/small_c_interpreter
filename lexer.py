import enum

class token_type(enum.Enum):
    """詞法分析後可產生的 token 類型。"""

    keyword = 1
    number = 2
    hexadecimal = 3
    string = 4
    char=5
    identifier = 6
    operator = 7
    punctuator = 8
    
class token:
    """單一 token 的資料結構：包含類型、行號與原始值。"""

    def __init__(self, type: token_type,line: int, value: str):
        self.type: token_type = type
        self.line: int = line
        self.value: str = value
keywords = ["int","char","void","if","else","while","for","return","do","continue","break"]
operators = ["!","~","+", "-", "*", "/", "%", "<", ">", "=", "&", "^", "|"]
operators_2 = ["++","--","==","!=","<=",">=","&&","||","<<",">>","+=","-=","*=","/=","%="]
punctuator= [";","(",")","{","}","[","]",",",".","?",":"]
class lexer:
    """將原始程式碼字串切分成 token 串列的詞法分析器。"""

    def __init__(self,codes: str):
        self.codes: str = codes
        self.position: int = 0
        self.line: int = 1
        self.macro_definitions: dict[str,str] = {}
        self.tokens: list[token] = []
    def _current_char(self):
        return self.codes[self.position]
    def _add_token(self, type: token_type, value: str):
        self.tokens.append(token(type,self.line,value))
    def _is_first_non_whitespace_on_line(self):
        position = self.position - 1
        while(position >= 0 and self.codes[position] != '\n'):
            if(not self.codes[position].isspace()):
                return False
            position-=1
        return True
    def _is_comment_start(self):
        return self.position+1 < len(self.codes) and self.codes[self.position:self.position+2] in ['/*','//']
    def _skip_whitespace(self):
        cur_token = self._current_char()
        if cur_token == '\n':
            self.line += 1
        self.position+=1
    def _skip_comment(self):
        # 單行註解
        if(self.codes[self.position:self.position+2]=='//'):
            # 直接前進到換行字元前
            while (self.position < len(self.codes) and self.codes[self.position] != '\n'):
                self.position+=1
        # 多行註解
        else:
            # 持續掃描直到遇到結尾 */
            while (self.position+1 < len(self.codes) and self.codes[self.position:self.position+2] != '*/'):
                if(self.codes[self.position] == '\n'):
                    self.line += 1
                self.position+=1
            if(self.position+1 >= len(self.codes)):
                raise Exception(f"Syntax error: Unterminated multi-line comment at line {self.line}")
            self.position+=2# 跳過結尾 */
    def _read_preprocessor_directive(self):
        # 前處理器指令必須是行首第一個非空白字元，否則視為語法錯誤
        if(not self._is_first_non_whitespace_on_line()):
            raise Exception(f"Syntax error: Preprocessor directive must be the first non-whitespace character on the line at line {self.line}")
        macro_type: str= ""
        macro_name: str = ""
        macro_value_str: str = ""
        # 先讀出 directive 類型（例如 #define）
        while (self.position < len(self.codes) and self.codes[self.position] != '\n' and self.codes[self.position] != ' ' and self.codes[self.position] != '\t'):
            macro_type += self.codes[self.position]
            self.position+=1
        if(self.position >= len(self.codes) or self.codes[self.position] == '\n'):
            raise Exception(f"Syntax error: Invalid preprocessor directive at line {self.line}: missing macro name and value")
        elif(macro_type != '#define'):
            raise Exception(f"Syntax error: Unsupported preprocessor directive: {macro_type} at line {self.line}")
        else:
            # 跳過空白與 tab
            while(self.position < len(self.codes) and (self.codes[self.position] == ' ' or self.codes[self.position] == '\t')):
                self.position+=1
            if(self.position >= len(self.codes) or self.codes[self.position] == '\n'):
                raise Exception(f"Syntax error: Invalid preprocessor directive at line {self.line}: missing macro name and value")
            # 讀取巨集名稱
            while (self.position < len(self.codes) and self.codes[self.position] != '\n' and self.codes[self.position] != ' ' and self.codes[self.position] != '\t'):
                # 巨集名稱必須是合法識別字
                if(self.codes[self.position].isalpha() or self.codes[self.position]=="_" or self.codes[self.position].isdigit() ):
                    macro_name += self.codes[self.position]
                    self.position+=1
                else:
                    raise Exception(f"Syntax error: Invalid macro character: {self.codes[self.position]} at line {self.line}")
            if(self.position >= len(self.codes) or self.codes[self.position] == '\n'):
                raise Exception(f"Syntax error: Invalid preprocessor directive at line {self.line}: missing macro value")
            elif(macro_name in self.macro_definitions):
                raise Exception(f"Syntax error: Duplicate macro definition: {macro_name} at line {self.line}")
            elif(macro_name in keywords):
                raise Exception(f"Syntax error: Macro name cannot be a keyword: {macro_name} at line {self.line}")
            elif(macro_name[0].isdigit()):
                raise Exception(f"Syntax error: Macro name cannot start with a digit: {macro_name} at line {self.line}")
            else:
                # 巨集值目前只允許數字（可含負號）
                # 跳過空白與 tab
                while(self.position < len(self.codes) and (self.codes[self.position] == ' ' or self.codes[self.position] == '\t')):
                    self.position+=1
                if(self.position >= len(self.codes) or self.codes[self.position] == '\n'):
                    raise Exception(f"Syntax error: Invalid preprocessor directive at line {self.line}: missing macro value")
                # 讀取巨集值（僅接受可選負號 + 數字）
                while (self.position < len(self.codes) and self.codes[self.position] != '\n' and self.codes[self.position] != ' ' and self.codes[self.position] != '\t'):
                    if(self.codes[self.position].isdigit() or (self.codes[self.position] == '-' and len(macro_value_str) == 0)):
                        macro_value_str += self.codes[self.position]
                        self.position+=1
                    else:
                        raise Exception(f"Syntax error: Invalid macro value: {macro_value_str} at line {self.line}")
                if(macro_value_str == '-' or macro_value_str == ''):
                    raise Exception(f"Syntax error: Invalid macro value: {macro_value_str} at line {self.line}")
                self.macro_definitions[macro_name] = macro_value_str
    def _read_operator(self):
        cur_token = self._current_char()
        oprator = cur_token
        self.position+=1
        # 若可組成雙字元運算子則一併吃掉下一字元
        if (self.position < len(self.codes) and self.codes[self.position-1:self.position+1] in operators_2):
            oprator += self.codes[self.position]
            self.position+=1
        self._add_token(token_type.operator,oprator)
    def _read_identifier_or_keyword(self):
        cur_token = self._current_char()
        ident=cur_token
        self.position+=1
        # 持續累積識別字後續字元
        while (self.position < len(self.codes) and (self.codes[self.position].isalpha() or self.codes[self.position].isdigit() or self.codes[self.position]=="_")):
            cur_token = self.codes[self.position]
            ident += cur_token
            self.position+=1
        if(ident in keywords):
            self._add_token(token_type.keyword,ident)
        else:
            if(ident in self.macro_definitions):
                # 在詞法分析階段直接展開巨集常數
                if(self.macro_definitions[ident].startswith('-')):
                    self._add_token(token_type.operator,'-')
                    self._add_token(token_type.number,self.macro_definitions[ident][1:])
                else:
                    self._add_token(token_type.number,self.macro_definitions[ident])
            else:
                self._add_token(token_type.identifier,ident)
    def _read_number(self):
        cur_token = self._current_char()
        num=cur_token
        self.position+=1
        # 檢查是否為十六進位（0x 前綴）
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
            # 十六進位常數結束後，若直接接字母或底線，視為非法後綴。
            if(self.position < len(self.codes) and (self.codes[self.position].isalpha() or self.codes[self.position] == '_')):
                raise Exception(f"Syntax error: Invalid suffix on hexadecimal constant at line {self.line}")
            self._add_token(token_type.hexadecimal,num)
        else:
            # 十進位數字
            while (self.position < len(self.codes) and self.codes[self.position].isdigit()):
                cur_token = self.codes[self.position]
                num += cur_token
                self.position+=1
            # 檢查數字後是否有非法字元（例如 123abc 或 123.45）
            if(self.position < len(self.codes) and (self.codes[self.position].isalpha() or self.codes[self.position] == '_')):
                raise Exception(f"Syntax error: Invalid suffix on integer constant at line {self.line}")
            self._add_token(token_type.number,num)
    def _read_string_or_char(self):
        cur_token = self._current_char()
        quote_type = cur_token
        string = ""
        self.position+=1
        while(self.position < len(self.codes) and self.codes[self.position] != quote_type):
            # 處理跳脫字元
            if(self.codes[self.position]=='\\'):
                # 反斜線後必須仍有字元，否則代表字串未結束
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
            elif(self.codes[self.position] == '\n'):# 字串常值不得跨行
                if(quote_type == '"'):
                    raise Exception(f"Syntax error: Unterminated string literal at line {self.line}")
                else:
                    raise Exception(f"Syntax error: Unterminated character literal at line {self.line}")
            else:
                string += self.codes[self.position]
            self.position+=1
        if(self.position >= len(self.codes)):
            if(quote_type == '"'):
                raise Exception(f"Syntax error: Unterminated string literal at line {self.line}")
            else:
                raise Exception(f"Syntax error: Unterminated character literal at line {self.line}")
        self.position+=1# 跳過結尾引號
        if(quote_type == "'" and len(string) != 1):
            raise Exception(f"Syntax error: Invalid character literal at line {self.line}: character literal must be a single character")
        if(quote_type == '"'):
            self._add_token(token_type.string,string)
        else:
            self._add_token(token_type.char,string)
    def _read_punctuator(self):
        cur_token = self._current_char()
        self.position+=1
        self._add_token(token_type.punctuator,cur_token)
    def tokenize(self):
        while self.position < len(self.codes):
            cur_token = self._current_char()
            # 跳過空白、換行與 tab
            if (cur_token.isspace()):# 包含空白、換行、tab 等所有 Unicode 空白字元
                self._skip_whitespace()
            # 註解
            elif(self._is_comment_start()):
                self._skip_comment()
            # 前處理器指令
            elif(cur_token == '#'):
                self._read_preprocessor_directive()
            elif(cur_token in operators):
                self._read_operator()
            # 關鍵字或識別字
            elif(cur_token.isalpha() or cur_token=="_"):
                self._read_identifier_or_keyword()
            # 十進位數字或十六進位數字
            elif(cur_token.isdigit()):
                self._read_number()
            # 字串/字元常值
            elif(cur_token == '"' or cur_token == "'"):
                self._read_string_or_char()
            # 分隔符號
            elif (cur_token in punctuator):
                self._read_punctuator()
            # 非預期字元
            else:
                raise Exception(f"Syntax error: Unexpected character: {cur_token}")
        return self.tokens
