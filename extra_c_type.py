# 額外的 C 型別，用來在解釋器中表示指標與陣列。
# 指標只保存目前地址；實際邊界檢查由 memory.VirtualMemory 的 allocation 資訊負責。


class char_ptr:
    """指向 char 的指標。

    addr : 目前指標值（所指向的記憶體位址）
    """
    def __init__(self, addr: int):
        self.addr = addr

    def __repr__(self):
        return f"char_ptr(addr={self.addr:#x})"


class int_ptr:
    """指向 int 的指標。

    addr : 目前指標值（所指向的記憶體位址）
    """
    def __init__(self, addr: int):
        self.addr = addr

    def __repr__(self):
        return f"int_ptr(addr={self.addr:#x})"


class array:
    """陣列，element_count 表示元素個數。"""
    def __init__(self, addr: int, element_count: int, elem_type: str):
        self.addr = addr        # 起始位址
        self.element_count = element_count    # 元素個數
        self.elem_type = elem_type

    def __repr__(self):
        return f"array(addr={self.addr:#x}, element_count={self.element_count}, elem_type={self.elem_type!r})"
