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


class ExpressionStmt:
    """運算式語句 AST 節點，例如 x = 1; 或 printf("hi");。

    這層包裝用來區分「真正的一個 statement」與 expression 內部節點，
    讓 TRACE 只印出語句執行，不會誤印 printf 參數或二元運算子節點。
    """

    def __init__(self, expr, line: int):
        self.expr = expr
        self.line = line

    def __repr__(self):
        return f"ExpressionStmt({self.expr})"


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

class InitList:
    """初始化列表 AST 節點，例如 {1, 2, 3}。"""

    def __init__(self, values: list, line):
        self.values = values
        self.line = line

    def __repr__(self):
        return f"InitList({self.values})"

class VarDecl:
    """變數宣告 AST 節點，例如 int x = 10;、int z; 或 int a[3] = {1, 2, 3};"""
    def __init__(self, var_type: str, name: str, init_expr, line: int, is_array=False, array_size=None):
        self.var_type = var_type   # "int" / "char" / "int*" / "char*"
        self.name = name           # 變數名稱
        self.init_expr = init_expr # 初始值運算式 (若無則為 None)
        self.line = line
        self.is_array = is_array # 是否為陣列宣告
        self.array_size = array_size # 明確指定的陣列大小；int a[] = {1, 2} 會保留 None，交由後續階段推導。

    def __repr__(self):
        if self.is_array:
            size = "" if self.array_size is None else self.array_size
            return f"VarDecl({self.var_type}, {self.name}[{size}], {self.init_expr})"
        return f"VarDecl({self.var_type}, {self.name}, {self.init_expr})"

class Param:
    """函式參數 AST 節點。

    param_type 使用和 VarDecl 相同的型別字串，例如 "int"、"char*"。
    陣列參數會保留 is_array / array_size，方便 interpreter 後續決定是否
    轉成指標語意。
    """
    def __init__(self, param_type: str, name: str, line: int, is_array=False, array_size=None):
        self.param_type = param_type
        self.name = name
        self.line = line
        self.is_array = is_array
        self.array_size = array_size

    def __repr__(self):
        if self.is_array:
            size = "" if self.array_size is None else self.array_size
            return f"Param({self.param_type}, {self.name}[{size}])"
        return f"Param({self.param_type}, {self.name})"

class FunctionDef:
    """函式定義 AST 節點。

    Small-C 不支援向前宣告，因此 parser 只建立 FunctionDef，
    不另外建立 FunctionDecl / Prototype 類型。
    """
    def __init__(self, return_type: str, name: str, params: list, body, line: int):
        self.return_type = return_type
        self.name = name
        self.params = params
        self.body = body
        self.line = line

    def __repr__(self):
        return f"FunctionDef({self.return_type}, {self.name}, {self.params}, {self.body})"

class Block:
    """區塊 AST 節點，代表由 { } 包起來的多個語句。"""
    def __init__(self, statements: list):
        self.statements = statements
    def __repr__(self):
        return f"Block({self.statements})"

class IfStmt:
    """If 條件分支 AST 節點。"""
    def __init__(self, condition, then_branch, else_branch=None, line: int = 0):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch  # 若無 else 則為 None
        self.line = line
    def __repr__(self):
        return f"IfStmt({self.condition}, {self.then_branch}, {self.else_branch})"

class WhileStmt:
    """While 迴圈 AST 節點。"""
    def __init__(self, condition, body, line: int = 0):
        self.condition = condition
        self.body = body
        self.line = line
    def __repr__(self):
        return f"WhileStmt({self.condition}, {self.body})"

class DoWhileStmt:
    """Do-while 迴圈 AST 節點。"""
    def __init__(self, body, condition, line: int = 0):
        self.body = body
        self.condition = condition
        self.line = line
    def __repr__(self):
        return f"DoWhileStmt({self.body}, {self.condition})"

class ForStmt:
    """For 迴圈 AST 節點，例如 for (init; condition; update) body。"""
    def __init__(self, init, condition, update, body, line: int = 0):
        self.init = init              # VarDecl / expression / None
        self.condition = condition    # expression / None，None 代表永遠成立
        self.update = update          # expression / None
        self.body = body              # 單一 statement 或 Block
        self.line = line
    def __repr__(self):
        return f"ForStmt({self.init}, {self.condition}, {self.update}, {self.body})"

class CaseClause:
    """switch 內的一個 case/default 區段。

    value 是 parser 階段折疊後的整數常數；default 使用 None。
    statements 保留該 label 後直到下一個 case/default 前的語句，供 interpreter 支援 fall-through。
    """
    def __init__(self, value, statements: list, line: int, is_default=False):
        self.value = value
        self.statements = statements
        self.line = line
        self.is_default = is_default
    def __repr__(self):
        label = "default" if self.is_default else f"case {self.value}"
        return f"CaseClause({label}, {self.statements})"

class SwitchStmt:
    """Switch 敘述 AST 節點，例如 switch (expr) { case 1: ... }。"""
    def __init__(self, expr, clauses: list[CaseClause], line: int):
        self.expr = expr
        self.clauses = clauses
        self.line = line
    def __repr__(self):
        return f"SwitchStmt({self.expr}, {self.clauses})"

class BreakStmt:
    """Break 敘述 AST 節點。"""
    def __init__(self, line):
        self.line = line
    def __repr__(self):
        return "BreakStmt()"

class ContinueStmt:
    """Continue 敘述 AST 節點。"""
    def __init__(self, line):
        self.line = line
    def __repr__(self):
        return "ContinueStmt()"

class ReturnStmt:
    """Return 敘述 AST 節點，支援 return; 與 return expression;。"""
    def __init__(self, expr, line):
        self.expr = expr
        self.line = line
    def __repr__(self):
        return f"ReturnStmt({self.expr})"

class EmptyStmt:
    """空敘述 AST 節點，代表單獨的分號 ;。"""
    def __init__(self, line):
        self.line = line
    def __repr__(self):
        return "EmptyStmt()"

class parser:
    """遞迴下降語法分析器，依照運算子優先權把 token 串轉成 AST。"""

    def __init__(self, tokens):
        """初始化 token 串、目前位置，以及目前正在看的 token。"""
        self.tokens: list[lexer.token] = tokens
        # position 指向 current_token 在 tokens 中的位置；讀完時 current_token 會是 None。
        self.position: int = 0
        self.current_token: lexer.token = self.peek()
        self.program = []  # 用來存放多行程式碼的 AST，讓 REPL 可以一次執行整段程式碼
        self.loop_depth: int = 0
        self.switch_depth: int = 0
        self.function_depth: int = 0

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

    def is_function_definition_start(self):
        """判斷目前位置是否看起來像函式定義的開頭。

        只用 lookahead，不消耗 token。符合以下形狀時回傳 True：
        int/char/void identifier (
        int*/char* identifier (
        """
        token = self.current_token
        if token is None or token.type != lexer.token_type.keyword or token.value not in ["int", "char", "void"]:
            return False

        # 回傳型別後面可以接一個 *，表示 int* / char* 回傳型別。
        offset = 1
        next_token = self.peek(offset)
        if next_token is not None and next_token.type == lexer.token_type.operator and next_token.value == "*":
            offset += 1

        name_token = self.peek(offset)
        paren_token = self.peek(offset + 1)
        return (
            name_token is not None
            and name_token.type == lexer.token_type.identifier
            and paren_token is not None
            and paren_token.type == lexer.token_type.punctuator
            and paren_token.value == "("
        )

    def is_declaration_start(self):
        """判斷目前 token 是否是變數宣告可能的開頭。"""
        token = self.current_token
        return (
            token is not None
            and token.type == lexer.token_type.keyword
            and token.value in ["int", "char", "void"]
        )

    def parse_type_spec(self, allow_void=False, context="type"):
        """解析型別名稱，並支援 int* / char*。

        allow_void 只應在解析函式回傳型別時設為 True。
        依目前規格，void 不能作為變數或參數型別，也不支援 void*。
        """
        token = self.current_token
        allowed = ["int", "char"]
        if allow_void:
            allowed.append("void")
        if token is None or token.type != lexer.token_type.keyword or token.value not in allowed:
            self.error(f"Expected {context}")

        parsed_type = token.value
        line = token.line
        self.advance()

        # Small-C 目前只支援 int* / char*，void* 不在作業規格內。
        if self.match("*", lexer.token_type.operator):
            if parsed_type == "void":
                self.error("void pointer type is not supported")
            parsed_type += "*"

        return parsed_type, line

    def parse_external_declaration(self):
        """解析最外層語法單元。

        Small-C 的最外層可以是：
        - 函式定義：int main() { ... }
        - 全域變數宣告：int x;
        - REPL 單行互動輸入沿用的一般 statement

        函式定義不是 statement，所以不要塞進 parse_statement() 當一般語句處理。
        """
        token = self.current_token
        if token is None:
            return None

        if token.type == lexer.token_type.keyword and token.value in ["int", "char", "void"]:
            if self.is_function_definition_start():
                return self.parse_function_def()
            if token.value == "void":
                self.error("void is only allowed as a function return type")

        # REPL 模式允許在 top-level 直接輸入 statement，例如 x = 1;。
        return self.parse_statement()

    def parse_statement(self):
        """解析一般語句，回傳對應 AST 節點。

        這個入口只處理可出現在區塊內的語法，例如 if、while、區塊、
        變數宣告與運算式語句。函式定義只能由 parse_external_declaration()
        在 top-level 解析。
        """
        token = self.current_token
        
        if token is None:
            return None

        # 1. 處理控制流程敘述
        if self.check("if", lexer.token_type.keyword):
            return self.parse_if_statement()
        if self.check("while", lexer.token_type.keyword):
            return self.parse_while_statement()
        if self.check("do", lexer.token_type.keyword):
            return self.parse_do_while_statement()
        if self.check("for", lexer.token_type.keyword):
            return self.parse_for_statement()
        if self.check("switch", lexer.token_type.keyword):
            return self.parse_switch_statement()
        if self.check("break", lexer.token_type.keyword):
            return self.parse_break_statement()
        if self.check("continue", lexer.token_type.keyword):
            return self.parse_continue_statement()
        if self.check("return", lexer.token_type.keyword):
            return self.parse_return_statement()
        if self.check("case", lexer.token_type.keyword):
            self.error("'case' label is only allowed directly inside a switch statement")
        if self.check("default", lexer.token_type.keyword):
            self.error("'default' label is only allowed directly inside a switch statement")

        # 2. 處理獨立的區塊 { ... }
        if self.check("{", lexer.token_type.punctuator):
            return self.parse_block()

        # 空敘述 ; 在 C 中是合法 statement，例如 if (x); 或 while (x);
        if self.check(";", lexer.token_type.punctuator):
            self.advance()
            return EmptyStmt(token.line)

        # 3. 處理變數宣告 (int, char, int*, char*)
        if token.type == lexer.token_type.keyword and token.value in ["int", "char", "void"]:
            if self.is_function_definition_start():
                self.error("Function definitions are only allowed at top level")
            if token.value == "void":
                self.error("void is only allowed as a function return type")
            return self.parse_var_decl()

        # 4. 若都不是以上情況，則視為運算式語句 (Expression Statement)
        expr = self.parse_expression()
        line = getattr(expr, "line", token.line)
        
        # C 語言中，除了特定的控制結構外，運算式語句結尾通常需要分號。
        # (例如函數呼叫 f(); 或賦值 x = 1;)
        self.expect(";", lexer.token_type.punctuator)
        return ExpressionStmt(expr, line)

    def parse(self):
        """解析整份輸入，依序回傳 top-level AST 節點。

        top-level 節點包含函式定義、全域變數宣告，以及 REPL 互動模式允許的
        單行 statement。
        """
        while not self.is_at_end():
            stmt = self.parse_external_declaration()
            self.program.append(stmt)
        return self.program

    def parse_function_def(self):
        """解析函式定義。

        支援：
            int main() { ... }
            char f(int x, char *s, int arr[]) { ... }
            void log(char msg[]) { ... }

        不支援：
            int f(int x);   # 向前宣告 / prototype
        """
        return_type, line = self.parse_type_spec(allow_void=True, context="function return type")

        # 回傳型別之後必須接函式名稱。
        name_token = self.current_token
        if name_token is None or name_token.type != lexer.token_type.identifier:
            self.error("Expected function name")
        name = name_token.value
        self.advance()

        self.expect("(", lexer.token_type.punctuator)
        params = self.parse_param_list()
        self.expect(")", lexer.token_type.punctuator)

        # Small-C 不支援 prototype；參數列表後面必須直接接函式本體。
        if self.check(";", lexer.token_type.punctuator):
            self.error("Forward function declarations are not supported; expected function body")
        if not self.check("{", lexer.token_type.punctuator):
            self.error("Expected function body")

        self.function_depth += 1
        try:
            body = self.parse_block()
        finally:
            self.function_depth -= 1
        return FunctionDef(return_type, name, params, body, line)

    def parse_param_list(self):
        """解析函式參數列表。

        空參數列表使用空 list 表示，例如 main() 或 main(void)。
        void 只允許單獨出現在參數列表中，代表「沒有參數」。
        """
        params = []
        if self.check(")", lexer.token_type.punctuator):
            return params

        if self.check("void", lexer.token_type.keyword):
            void_token = self.advance()
            if not self.check(")", lexer.token_type.punctuator):
                self.error("void parameter list must not contain other parameters", void_token)
            return params

        while True:
            params.append(self.parse_param())
            if self.match(",", lexer.token_type.punctuator) is None:
                break
            if self.check(")", lexer.token_type.punctuator):
                self.error("Trailing comma is not allowed in parameter list")

        return params

    def parse_param(self):
        """解析單一函式參數。

        允許基本型別、指標參數與一維陣列參數：
            int x
            char *s
            int arr[]
            char buf[8]
        """
        param_type, line = self.parse_type_spec(allow_void=False, context="parameter type")

        name_token = self.current_token
        if name_token is None or name_token.type != lexer.token_type.identifier:
            self.error("Expected parameter name")
        name = name_token.value
        self.advance()

        # 參數只支援一維陣列形式：int a[] 或 int a[10]。
        is_array = False
        array_size = None
        if self.match("[", lexer.token_type.punctuator):
            is_array = True
            if self.check("]", lexer.token_type.punctuator):
                self.advance()
            else:
                size_token = self.current_token
                if size_token is None or size_token.type != lexer.token_type.number:
                    self.error("Expected decimal array size")
                array_size = int(size_token.value)
                if array_size <= 0:
                    self.error("Array size must be greater than 0", size_token)
                self.advance()
                self.expect("]", lexer.token_type.punctuator)

        return Param(param_type, name, line, is_array, array_size)

    def parse_var_decl(self):
        """解析變數或陣列宣告，支援 int a;、int a[3];、int a[] = {1, 2, 3};。"""
        # 宣告格式固定從型別開始，例如 int x;、char c;、int* p;。
        type_token = self.current_token
        var_type = type_token.value
        line = type_token.line
        self.advance() # 吃掉型別關鍵字

        # C 語言中，變數宣告可以有指標，例如 int* p; 或 char* s;。
        if self.match("*", lexer.token_type.operator):
            var_type += "*"

        name_token = self.current_token
        if name_token is None or name_token.type != lexer.token_type.identifier:
            self.error("Expected variable name")
        name = name_token.value
        self.advance() # 吃掉變數名稱

        # 變數名稱後若接 [] 或 [size]，代表這是陣列宣告。
        # 目前 size 只允許十進位整數常數，避免在 parser 階段求值 expression。
        is_array = False
        array_size = None
        if self.match("[", lexer.token_type.punctuator):
            is_array = True
            if self.check("]", lexer.token_type.punctuator):
                self.advance()
            else:
                size_token = self.current_token
                if size_token is None or size_token.type != lexer.token_type.number:
                    self.error("Expected decimal array size")
                array_size = int(size_token.value)
                if array_size <= 0:
                    self.error("Array size must be greater than 0", size_token)
                self.advance()
                self.expect("]", lexer.token_type.punctuator)

        # 一般變數用 expression 初始化；陣列可以用 { ... } 初始化列表。
        init_expr = None
        if self.match("=", lexer.token_type.operator):
            if self.check("{", lexer.token_type.punctuator):
                init_expr = self.parse_init_list()
            else:
                init_expr = self.parse_expression()

        if is_array:
            # 陣列定義支援初始化列表；char 陣列也支援字串常數初始化。
            if isinstance(init_expr, String):
                # C 中只有 char 陣列能用字串常數初始化，例如 char s[] = "abc"。
                if var_type != "char":
                    self.error("String initializer is only valid for char arrays")
                # 顯式大小可剛好容納字串內容；若要保留結尾 \0，使用者需多留一格。
                if array_size is not None and len(init_expr.value) > array_size:
                    self.error("String initializer is larger than array size")
                if array_size is None:
                    # char s[] = "abc" 會推導成 4，包含字串結尾的 \0。
                    array_size = len(init_expr.value) + 1
            # 除了字串常數以外的陣列初始化都必須是初始化列表，例如 int a[3] = {1, 2, 3}；不允許 int a[3] = 1。
            elif init_expr is not None and not isinstance(init_expr, InitList):
                self.error("Array initializer must be an initializer list")
            # int a[]; 無法從語法資訊得知大小，因此要求必須提供初始化列表。
            if array_size is None and init_expr is None:
                self.error("Array declaration with [] requires an initializer")
            # int a[] = {}; 也無法推導出合法大小。
            if array_size is None and isinstance(init_expr, InitList) and len(init_expr.values) == 0:
                self.error("Array declaration with [] requires a non-empty initializer list")
            if array_size is not None and isinstance(init_expr, InitList) and len(init_expr.values) > array_size:
                self.error("Array initializer has more values than array size")
            if array_size is None and isinstance(init_expr, InitList):
                # int a[] = {1, 2, 3} 直接由初始化列表長度推導大小。
                array_size = len(init_expr.values)

        self.expect(";", lexer.token_type.punctuator)
        return VarDecl(var_type, name, init_expr, line, is_array, array_size)

    def parse_init_list(self):
        """解析初始化列表 { expr, expr, ... }，不允許尾端逗號。"""
        brace_token = self.expect("{", lexer.token_type.punctuator)
        values = []

        if not self.check("}", lexer.token_type.punctuator):
            while True:
                values.append(self.parse_expression())
                if self.match(",", lexer.token_type.punctuator) is None:
                    break
                if self.check("}", lexer.token_type.punctuator):
                    self.error("Trailing comma is not allowed in initializer list")

        self.expect("}", lexer.token_type.punctuator)
        return InitList(values, brace_token.line)

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
        """第 2 級：前綴一元運算 +、-、!、~、*、&、++、--，右結合。"""
        operator = self.match_operator({"+", "-", "!", "~", "*", "&", "++", "--"})
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
                if not isinstance(expr, Identifier):
                    self.error("Syntax error: Function call must be applied to an identifier", paren_token)
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
            statements.append(self.parse_statement()) # 遞迴呼叫parse_statement()處理單句
            
        self.expect("}", lexer.token_type.punctuator)
        return Block(statements)

    def parse_if_statement(self):
        """解析 if (cond) { ... } else { ... }"""
        if_token = self.advance() # 吃掉 'if'
        self.expect("(", lexer.token_type.punctuator)
        condition = self.parse_expression()
        self.expect(")", lexer.token_type.punctuator)
        
        # 解析 if 成立時要執行的語句 (通常是 parse_block，但也支援單行不加括號)
        then_branch = self.parse_statement_or_block()
        
        else_branch = None
        # 如果有 else，繼續解析
        if self.match("else", lexer.token_type.keyword):
            else_branch = self.parse_statement_or_block()

        return IfStmt(condition, then_branch, else_branch, if_token.line)

    def parse_while_statement(self):
        """解析 while (cond) { ... }"""
        while_token = self.advance() # 吃掉 'while'
        self.expect("(", lexer.token_type.punctuator)
        condition = self.parse_expression()
        self.expect(")", lexer.token_type.punctuator)

        self.loop_depth += 1
        try:
            body = self.parse_statement_or_block()
        finally:
            self.loop_depth -= 1
        return WhileStmt(condition, body, while_token.line)

    def parse_do_while_statement(self):
        """解析 do { ... } while (cond);"""
        do_token = self.advance() # 吃掉 'do'

        self.loop_depth += 1
        try:
            body = self.parse_statement_or_block()
        finally:
            self.loop_depth -= 1

        self.expect("while", lexer.token_type.keyword)
        self.expect("(", lexer.token_type.punctuator)
        condition = self.parse_expression()
        self.expect(")", lexer.token_type.punctuator)
        self.expect(";", lexer.token_type.punctuator)
        return DoWhileStmt(body, condition, do_token.line)

    def parse_for_statement(self):
        """解析 for (init; condition; update) body"""
        for_token = self.advance() # 吃掉 'for'
        self.expect("(", lexer.token_type.punctuator)

        init = None
        if self.check(";", lexer.token_type.punctuator):
            self.advance()
        elif self.current_token is not None and self.current_token.type == lexer.token_type.keyword and self.current_token.value in ["int", "char"]:
            # for 的 init 可是變數宣告；parse_statement 會一併吃掉結尾分號。
            init = self.parse_statement()
        # 否則 init 是一般的 expression，結尾分號要自己吃掉。
        else:
            init = self.parse_expression()
            self.expect(";", lexer.token_type.punctuator)

        condition = None
        if not self.check(";", lexer.token_type.punctuator):
            condition = self.parse_expression()
        self.expect(";", lexer.token_type.punctuator)

        update = None
        if not self.check(")", lexer.token_type.punctuator):
            update = self.parse_expression()
        self.expect(")", lexer.token_type.punctuator)

        self.loop_depth += 1
        try:
            body = self.parse_statement_or_block()
        finally:
            self.loop_depth -= 1
        return ForStmt(init, condition, update, body, for_token.line)

    def parse_switch_statement(self):
        """解析 switch (expr) { case CONST: ... default: ... }。

        case label 在這裡會被折疊成 compile-time integer constant，接近 C 的限制；
        switch 本身的控制 expression 仍保留為一般 runtime expression。
        """
        switch_token = self.advance() # 吃掉 'switch'
        self.expect("(", lexer.token_type.punctuator)
        expr = self.parse_expression()
        self.expect(")", lexer.token_type.punctuator)
        self.expect("{", lexer.token_type.punctuator)

        clauses = []
        seen_cases = set()
        seen_default = False

        self.switch_depth += 1
        try:
            while not self.check("}", lexer.token_type.punctuator) and not self.is_at_end():
                if self.check("case", lexer.token_type.keyword):
                    clause = self.parse_case_clause()
                    if clause.value in seen_cases:
                        raise Exception(f"Syntax error: Duplicate case label {clause.value} at line {clause.line}")
                    seen_cases.add(clause.value)
                    clauses.append(clause)
                elif self.check("default", lexer.token_type.keyword):
                    if seen_default:
                        token = self.current_token
                        raise Exception(f"Syntax error: Duplicate default label at line {token.line}")
                    seen_default = True
                    clauses.append(self.parse_default_clause())
                elif self.check(";", lexer.token_type.punctuator):
                    # 放寬 switch body 最外層的空敘述；lexer 不保留空白行，真正會留下來的是單獨的 ';'。
                    self.advance()
                else:
                    # 除了空敘述外，switch body 最外層仍必須由 case/default label 組成，避免 label 前語句語意模糊。
                    self.error("Expected 'case' or 'default' label in switch statement")
            self.expect("}", lexer.token_type.punctuator)
        finally:
            self.switch_depth -= 1

        return SwitchStmt(expr, clauses, switch_token.line)

    def parse_case_clause(self):
        """解析單一 case 區段，並把 label 驗證為整數常數表達式。"""
        case_token = self.advance() # 吃掉 'case'
        value_expr = self.parse_expression()
        value = self.fold_int_constant_expr(value_expr, case_token.line)
        self.expect(":", lexer.token_type.punctuator)
        return CaseClause(value, self.parse_switch_clause_statements(), case_token.line)

    def parse_default_clause(self):
        """解析單一 default 區段。"""
        default_token = self.advance() # 吃掉 'default'
        self.expect(":", lexer.token_type.punctuator)
        return CaseClause(None, self.parse_switch_clause_statements(), default_token.line, is_default=True)

    def parse_switch_clause_statements(self):
        """收集目前 case/default 後方的語句，直到下一個 label 或 switch 結尾。"""
        statements = []
        while (
            not self.is_at_end()
            and not self.check("case", lexer.token_type.keyword)
            and not self.check("default", lexer.token_type.keyword)
            and not self.check("}", lexer.token_type.punctuator)
        ):
            if not statements and self.is_declaration_start():
                self.error("Variable declaration directly after case/default label must be inside a block; use '{ ... }'")
            statements.append(self.parse_statement())
        return statements

    def fold_int_constant_expr(self, expr, line: int) -> int:
        """將 case label 的 AST 折疊成 int；遇到變數、函式呼叫等 runtime expression 就報錯。"""
        if isinstance(expr, Number):
            return expr.value
        if isinstance(expr, Char):
            return ord(expr.value)
        if isinstance(expr, UnaryExpr):
            value = self.fold_int_constant_expr(expr.operand, line)
            if expr.operator == "+":
                return value
            if expr.operator == "-":
                return -value
            if expr.operator == "~":
                return ~value
            if expr.operator == "!":
                return 0 if value else 1
            raise Exception(f"Syntax error: Unsupported unary operator '{expr.operator}' in case label at line {line}")
        if isinstance(expr, BinaryExpr):
            left = self.fold_int_constant_expr(expr.left, line)
            # 常數表達式中的邏輯運算仍保留 C-like 短路，避免 1 || (1 / 0) 誤觸右側錯誤。
            if expr.operator == "&&":
                if not left:
                    return 0
                right = self.fold_int_constant_expr(expr.right, line)
                return 1 if right else 0
            if expr.operator == "||":
                if left:
                    return 1
                right = self.fold_int_constant_expr(expr.right, line)
                return 1 if right else 0
            right = self.fold_int_constant_expr(expr.right, line)
            return self.fold_int_constant_binary(expr.operator, left, right, line)
        raise Exception(f"Syntax error: case label must be an integer constant expression at line {line}")

    def fold_int_constant_binary(self, operator: str, left: int, right: int, line: int) -> int:
        """處理 case 常數表達式中的二元運算，使用 C-like 整數除法與餘數。"""
        if operator == "+":
            return left + right
        if operator == "-":
            return left - right
        if operator == "*":
            return left * right
        if operator == "/":
            if right == 0:
                raise Exception(f"Syntax error: Division by zero in case label at line {line}")
            quotient = abs(left) // abs(right)
            return -quotient if (left < 0) != (right < 0) else quotient
        if operator == "%":
            if right == 0:
                raise Exception(f"Syntax error: Modulo by zero in case label at line {line}")
            quotient = abs(left) // abs(right)
            quotient = -quotient if (left < 0) != (right < 0) else quotient
            return left - quotient * right
        if operator == "<<":
            # Python 對負數 shift count 會丟 ValueError；這裡先轉成 Small-C 的語法錯誤格式。
            if right < 0:
                raise Exception(f"Syntax error: Negative shift count in case label at line {line}")
            return left << right
        if operator == ">>":
            # 同上，避免 case 常數折疊時漏出 Python 原生錯誤訊息。
            if right < 0:
                raise Exception(f"Syntax error: Negative shift count in case label at line {line}")
            return left >> right
        if operator == "<":
            return 1 if left < right else 0
        if operator == "<=":
            return 1 if left <= right else 0
        if operator == ">":
            return 1 if left > right else 0
        if operator == ">=":
            return 1 if left >= right else 0
        if operator == "==":
            return 1 if left == right else 0
        if operator == "!=":
            return 1 if left != right else 0
        if operator == "&":
            return left & right
        if operator == "^":
            return left ^ right
        if operator == "|":
            return left | right
        # && / || 已在 fold_int_constant_expr() 先做短路處理；這裡只保留防禦式 fallback。
        if operator == "&&":
            return 1 if left and right else 0
        if operator == "||":
            return 1 if left or right else 0
        raise Exception(f"Syntax error: Unsupported operator '{operator}' in case label at line {line}")

    def parse_break_statement(self):
        """解析 break;"""
        if self.loop_depth == 0 and self.switch_depth == 0:
            self.error("'break' statement is only allowed inside a loop or switch")
        token = self.advance() # 吃掉 'break'
        self.expect(";", lexer.token_type.punctuator)
        return BreakStmt(token.line)

    def parse_continue_statement(self):
        """解析 continue;"""
        if self.loop_depth == 0:
            self.error("'continue' statement is only allowed inside a loop")
        token = self.advance() # 吃掉 'continue'
        self.expect(";", lexer.token_type.punctuator)
        return ContinueStmt(token.line)

    def parse_return_statement(self):
        """解析 return; 或 return expression;，只能出現在函式本體內。"""
        if self.function_depth == 0:
            self.error("'return' statement is only allowed inside a function")

        token = self.advance() # 吃掉 'return'
        expr = None
        if not self.check(";", lexer.token_type.punctuator):
            expr = self.parse_expression()
        self.expect(";", lexer.token_type.punctuator)
        return ReturnStmt(expr, token.line)

    def parse_statement_or_block(self):
        """輔助函式：判斷接下來是 { 區塊，還是單行語句"""
        if self.is_at_end():
            self.error("Expected statement")
        if self.check("{", lexer.token_type.punctuator):
            return self.parse_block()
        if self.is_declaration_start():
            self.error("Variable declaration in a control statement body must be inside a block; use '{ ... }'")
        return self.parse_statement()
