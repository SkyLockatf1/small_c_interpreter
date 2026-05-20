# 額外的 C 型別，用來在解釋器中表示指標與陣列，讓 builtins 可以做精確的邊界檢查。


class char_ptr:
    """指向 char 的指標。

    addr      : 目前指標值（所指向的記憶體位址）
    base_addr : 所屬 buffer 的起始位址，供邊界檢查使用（預設等於 addr）
    length    : 所屬 buffer 的位元組大小，0 表示未知
    """
    def __init__(self, addr: int, base_addr: int = None, length: int = 0):
        self.addr = addr
        self.base_addr = base_addr if base_addr is not None else addr
        self.length = length

    def __repr__(self):
        return f"char_ptr(addr={self.addr:#x}, base={self.base_addr:#x}, len={self.length})"


class int_ptr:
    """指向 int 的指標。

    addr      : 目前指標值（所指向的記憶體位址）
    base_addr : 所屬 buffer 的起始位址，供邊界檢查使用（預設等於 addr）
    length    : 所屬 buffer 的位元組大小，0 表示未知
    """
    def __init__(self, addr: int, base_addr: int = None, length: int = 0):
        self.addr = addr
        self.base_addr = base_addr if base_addr is not None else addr
        self.length = length

    def __repr__(self):
        return f"int_ptr(addr={self.addr:#x}, base={self.base_addr:#x}, len={self.length})"


class array:
    """陣列（保持不變，已有 addr / length / elem_type）。"""
    def __init__(self, addr: int, length: int, elem_type: str):
        self.addr = addr        # 起始位址
        self.length = length    # 元素個數
        self.elem_type = elem_type

    def __repr__(self):
        return f"array(addr={self.addr:#x}, length={self.length}, elem_type={self.elem_type!r})"
