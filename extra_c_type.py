# 這裡定義一些額外的 C 類型，像是 char* 和 int*，用來在解釋器中表示指標類型。
class char_ptr:
    def __init__(self, addr: int, length: int):
        self.addr = addr
    def __repr__(self):
        return f"char_ptr({self.addr:#x})"
class int_ptr:
    def __init__(self, addr: int):
        self.addr = addr
    def __repr__(self):
        return f"int_ptr({self.addr:#x})"
class array:
    def __init__(self, addr: int, length: int, elem_type):
        self.addr = addr # 起始位址
        self.length = length
        self.elem_type = elem_type
    def __repr__(self):
        return f"array({self.addr:#x}, {self.length}, {self.elem_type})"