import lexer


class Number:
    """整數常數 AST 節點。"""

    def __init__(self, value, line):
        self.value = value
        self.line = line
    def __repr__(self):
        return f"Number({self.value})"


class Char:
    """字元常數 AST 節點。"""

    def __init__(self, char: str, line):
        self.value: str = char
        self.line = line
    def __repr__(self):
        return f"Char('{self.value}')"


class String:
    """字串常數 AST 節點。"""

    def __init__(self, string: str, line):
        self.value: str = string
        self.line = line
    def __repr__(self):
        return f'String("{self.value}")'

class Identifier:
    """識別字 AST 節點，代表變數名稱或函式名稱。"""

    def __init__(self, name: str, line):
        self.name = name
        self.line = line
    def __repr__(self):
        return f"Identifier({self.name})"


class Pointer:
    """指標 AST 節點。"""

    def __init__(self, dtype, value, line):
        self.dtype = dtype
        self.value = value
        self.line = line
    def __repr__(self):
        return f"Pointer({self.dtype}, {self.value})"


class BinaryExpr:
    """二元運算 AST 節點，例如 +、*、==、&&、|。"""

    def __init__(self, left, operator, right, line):
        self.left = left
        self.operator: str = operator
        self.right = right
        self.line = line
    def __repr__(self):
        return f"BinaryExpr({self.left}, {self.operator}, {self.right})"


class UnaryExpr:
    """一元運算 AST 節點，例如 -x、!x、*p、&x、++x。"""

    def __init__(self, operator: str, operand, line, postfix=False):
        self.operator = operator
        self.operand = operand
        self.postfix = postfix
        self.line = line
    def __repr__(self):
        return f"UnaryExpr({self.operator}, {self.operand}, postfix={self.postfix})"


class AssignmentExpr:
    """指定運算 AST 節點，例如 =、+=、-=、*=、/=、%=。"""

    def __init__(self, left, operator: str, right, line):
        self.left = left
        self.operator = operator
        self.right = right
        self.line = line
    def __repr__(self):
        return f"AssignmentExpr({self.left}, {self.operator}, {self.right})"


class CallExpr:
    """函式呼叫 AST 節點，例如 f(a, b)。"""

    def __init__(self, fn, args, line):
        self.fn = fn
        self.args = args
        self.line = line
    def __repr__(self):
        return f"CallExpr({self.fn}, {self.args})"

class IndexExpr:
    """陣列索引 AST 節點，例如 arr[i]。"""

    def __init__(self, base, index, line):
        self.base = base
        self.index = index
        self.line = line
    def __repr__(self):
        return f"IndexExpr({self.base}, {self.index})"

class VarDecl:
    """變數宣告 AST 節點，例如 int x = 10; 或 int z;"""
    def __init__(self, var_type: str, name: str, init_expr, line: int):
        self.var_type = var_type   # "int" 或 "char"
        self.name = name           # 變數名稱
        self.init_expr = init_expr # 初始值運算式 (若無則為 None)
        self.line = line

    def __repr__(self):
        return f"VarDecl({self.var_type}, {self.name}, {self.init_expr})"
# class TypeSpec:
#     """型別描述 AST 節點，例如 int、char*、void。"""

#     def __init__(self, base_type: str, pointer_level: int = 0):
#         self.base_type = base_type
#         self.pointer_level = pointer_level

class Block:
    """區塊 AST 節點，代表由 { } 包起來的多個語句。"""
    def __init__(self, statements: list):
        self.statements = statements
    def __repr__(self):
        return f"Block({self.statements})"

class IfStmt:
    """If 條件分支 AST 節點。"""
    def __init__(self, condition, then_branch, else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch  # 若無 else 則為 None
    def __repr__(self):
        return f"IfStmt({self.condition}, {self.then_branch}, {self.else_branch})"

class parser:
    """遞迴下降語法分析器，依照運算子優先權把 token 串轉成 AST。"""

    def __init__(self, tokens):
        """初始化 token 串、目前位置，以及目前正在看的 token。"""
        self.tokens: list[lexer.token] = tokens
        # position 指向 current_token 在 tokens 中的位置；讀完時 current_token 會是 None。
        self.position: int = 0
        self.current_token: lexer.token = self.peek()
        self.statements = []  # 用來存放多行程式碼的 AST，讓 REPL 可以一次執行整段程式碼

    def peek(self, offset=0):
        """查看目前 token 或往後 offset 個位置的 token，但不改變 parser 狀態。"""
        return self.tokens[self.position + offset] if 0 <= self.position + offset < len(self.tokens) else None

    def advance(self):
        """吃掉目前 token，位置往前進一格，並回傳被吃掉的 token。"""
        token = self.current_token
        if self.position < len(self.tokens):
            self.position += 1
        # 每次移動後都重新同步 current_token，避免位置與目前 token 不一致。
        self.current_token = self.peek()
        return token

    def is_at_end(self):
        """判斷 token 是否已經全部讀完。"""
        return self.current_token is None

    def error(self, message, token=None):
        """統一產生語法錯誤訊息，盡量附上出錯行號與 token 值。"""
        token = self.current_token if token is None else token
        if token is None:
            raise Exception(f"Syntax error: {message} at end of input")
        raise Exception(f"Syntax error: {message} at line {token.line}: got '{token.value}'")

    def check(self, value, token_type=None):
        """檢查目前 token 是否符合指定 value 與可選的 token_type，但不消耗 token。"""
        token = self.current_token
        if token is None:
            return False
        # token_type 有傳入時才檢查類別，讓呼叫端也能只比對 token 文字。
        if token_type is not None and token.type != token_type:
            return False
        return token.value == value

    def match(self, value, token_type=None):
        """如果目前 token 符合條件就吃掉並回傳，否則回傳 None。"""
        if self.check(value, token_type):
            return self.advance()
        return None

    def expect(self, value, token_type=None):
        """要求目前 token 必須符合條件；不符合時直接報語法錯誤。"""
        token = self.match(value, token_type)
        if token is None:
            self.error(f"Expected token '{value}'")
        return token

    def match_operator(self, operators):
        """如果目前 token 是指定集合中的運算子，就吃掉並回傳該 token。"""
        token = self.current_token
        if token is not None and token.type == lexer.token_type.operator and token.value in operators:
            return self.advance()
        return None

    def parse_statement(self):
        """解析單一語句（If、區塊、變數宣告或運算式語句），回傳對應 AST 節點。"""
        token = self.current_token
        
        if token is None:
            return None

        # 1. 處理 If 敘述
        if token.type == lexer.token_type.keyword and token.value == "if":
            return self.parse_if_statement()

        # 2. 處理獨立的區塊 { ... }
        if token.type == lexer.token_type.punctuator and token.value == "{":
            return self.parse_block()

        # 3. 處理變數宣告 (int, char)
        if token.type == lexer.token_type.keyword and token.value in ["int", "char"]:
            var_type = token.value
            line = token.line
            self.advance() # 吃掉型別關鍵字

            name_token = self.current_token
            if name_token is None or name_token.type != lexer.token_type.identifier:
                self.error("Expected variable name")
            name = name_token.value
            self.advance() # 吃掉變數名稱

            init_expr = None
            if self.match("=", lexer.token_type.operator):
                init_expr = self.parse_expression()

            self.expect(";", lexer.token_type.punctuator)
            return VarDecl(var_type, name, init_expr, line)

        # 4. 若都不是以上情況，則視為運算式語句 (Expression Statement)
        expr = self.parse_expression()
        
        # C 語言中，除了特定的控制結構外，運算式語句結尾通常需要分號。
        # (例如函數呼叫 f(); 或賦值 x = 1;)
        self.expect(";", lexer.token_type.punctuator)
        return expr

    def parse(self):
        """解析所有語句，每個語句的 AST 依序存入 self.statements 並回傳該 list。"""
        while not self.is_at_end():
            stmt = self.parse_statement()
            self.statements.append(stmt)
        return self.statements

    def parse_expression(self):
        """運算式入口，目前最低層級是指定運算。"""
        return self.parse_assignment()

    def parse_assignment(self):
        """第 13 級：指定運算 =、+=、-=、*=、/=、%=，右結合。"""
        left = self.parse_logical_or()
        operator = self.match_operator({"=", "+=", "-=", "*=", "/=", "%="})
        if operator is not None:
            # 指定運算是右結合，所以右側再次呼叫 parse_assignment。
            right = self.parse_assignment()
            return AssignmentExpr(left, operator.value, right, operator.line)
        return left

    def parse_logical_or(self):
        """第 12 級：邏輯 OR ||，左結合；短路求值由 interpreter 負責。"""
        return self.parse_binary_left(self.parse_logical_and, {"||"})

    def parse_logical_and(self):
        """第 11 級：邏輯 AND &&，左結合；短路求值由 interpreter 負責。"""
        return self.parse_binary_left(self.parse_bitwise_or, {"&&"})

    def parse_bitwise_or(self):
        """第 10 級：位元 OR |，左結合。"""
        return self.parse_binary_left(self.parse_bitwise_xor, {"|"})

    def parse_bitwise_xor(self):
        """第 9 級：位元 XOR ^，左結合。"""
        return self.parse_binary_left(self.parse_bitwise_and, {"^"})

    def parse_bitwise_and(self):
        """第 8 級：位元 AND &，左結合。"""
        return self.parse_binary_left(self.parse_equality, {"&"})

    def parse_equality(self):
        """第 7 級：相等運算 ==、!=，左結合。"""
        return self.parse_binary_left(self.parse_relational, {"==", "!="})

    def parse_relational(self):
        """第 6 級：關係運算 <、<=、>、>=，左結合。"""
        return self.parse_binary_left(self.parse_shift, {"<", "<=", ">", ">="})

    def parse_shift(self):
        """第 5 級：位移運算 <<、>>，左結合。"""
        return self.parse_binary_left(self.parse_additive, {"<<", ">>"})

    def parse_additive(self):
        """第 4 級：加減運算 +、-，左結合。"""
        return self.parse_binary_left(self.parse_multiplicative, {"+", "-"})

    def parse_multiplicative(self):
        """第 3 級：乘除餘數 *、/、%，左結合。"""
        return self.parse_binary_left(self.parse_unary, {"*", "/", "%"})

    def parse_binary_left(self, parse_operand, operators):
        """共用的左結合二元運算 parser。"""
        expr = parse_operand() #先處理左邊
        # 左結合用 while 連續吃同一層級的運算子，逐步把左側 AST 包起來。
        while True:
            operator = self.match_operator(operators)
            if operator is None:
                break
            right = parse_operand()
            expr = BinaryExpr(expr, operator.value, right, operator.line)
        return expr

    def parse_unary(self):
        """第 2 級：前綴一元運算 -、!、~、*、&、++、--，右結合。"""
        operator = self.match_operator({"-", "!", "~", "*", "&", "++", "--"})
        if operator is not None:
            # 一元運算是右結合，因此 operand 繼續解析 parse_unary。
            return UnaryExpr(operator.value, self.parse_unary(), operator.line)
        return self.parse_postfix()

    def parse_postfix(self):
        """第 1 級：後綴函式呼叫 () 與陣列索引 []，左結合且可連續出現。"""
        expr = self.parse_primary()
        # 後綴運算優先權最高，像 f()[i](x) 會從左到右一層層包成 AST。
        while True:
            paren_token = self.match("(", lexer.token_type.punctuator)
            if paren_token:
                args = []
                if not self.check(")", lexer.token_type.punctuator):
                    # 參數本身也是完整 expression，所以可包含指定與所有二元運算。
                    while True:
                        args.append(self.parse_expression())
                        if self.match(",", lexer.token_type.punctuator) is None:
                            break
                self.expect(")", lexer.token_type.punctuator)
                expr = CallExpr(expr, args, paren_token.line)
            else:
                bracket_token = self.match("[", lexer.token_type.punctuator)
                if bracket_token:
                    # 索引值也是完整 expression，例如 arr[i + 1]。
                    index = self.parse_expression()
                    self.expect("]", lexer.token_type.punctuator)
                    expr = IndexExpr(expr, index, bracket_token.line)
                else:
                    break
        return expr

    def parse_primary(self):
        """解析最基本的 expression：常數、識別字，或用括號包起來的子運算式。"""
        token = self.current_token
        if token is None:
            self.error("Expected expression")

        if token.type == lexer.token_type.number:
            # 十進位整數常數。
            self.advance()
            return Number(int(token.value), token.line)
        if token.type == lexer.token_type.hexadecimal:
            # 十六進位整數常數，例如 0x10。
            self.advance()
            return Number(int(token.value, 16), token.line)
        if token.type == lexer.token_type.char:
            # 字元常數，例如 'a'。
            self.advance()
            return Char(token.value, token.line)
        if token.type == lexer.token_type.string:
            # 字串常數，例如 "hello"。
            self.advance()
            return String(token.value, token.line)
        if token.type == lexer.token_type.identifier:
            # 變數名稱或函式名稱；是否存在由後續語意分析或執行階段檢查。
            self.advance()
            return Identifier(token.value, token.line)
        if self.match("(", lexer.token_type.punctuator):
            # 括號會重設優先權，內部用完整 expression 入口重新解析。
            expr = self.parse_expression()
            self.expect(")", lexer.token_type.punctuator)
            return expr

        self.error("Expected expression", token)
    def parse_block(self):
        """解析大括號區塊 { ... }"""
        self.advance() # 吃掉 '{'
        statements = []
        # 一直解析語句，直到遇到 '}' 或檔案結束
        while not self.check("}", lexer.token_type.punctuator) and not self.is_at_end():
            statements.append(self.parse()) # 遞迴呼叫你之前寫好的 parse()
            
        self.expect("}", lexer.token_type.punctuator)
        return Block(statements)

    def parse_if_statement(self):
        """解析 if (cond) { ... } else { ... }"""
        self.advance() # 吃掉 'if'
        self.expect("(", lexer.token_type.punctuator)
        condition = self.parse_expression()
        self.expect(")", lexer.token_type.punctuator)
        
        # 解析 if 成立時要執行的語句 (通常是 parse_block，但也支援單行不加括號)
        then_branch = self.parse_statement_or_block()
        
        else_branch = None
        # 如果有 else，繼續解析
        if self.match("else", lexer.token_type.keyword):
            else_branch = self.parse_statement_or_block()
            
        return IfStmt(condition, then_branch, else_branch)

    def parse_statement_or_block(self):
        """輔助函式：判斷接下來是 { 區塊，還是單行語句"""
        if self.check("{", lexer.token_type.punctuator):
            return self.parse_block()
        else:
            return self.parse()
    