# symtable.py
class symtable:
    def __init__(self):
        # table 負責記錄: 變數名稱 -> {'type': 型別, 'addr': 記憶體位址}
        self.table = {}

    def define(self, name: str, var_type: str, addr: int):
        """宣告新變數並記錄其記憶體位址"""
        if name in self.table:
            raise Exception(f"Runtime error: Variable '{name}' is already defined.")
        self.table[name] = {'type': var_type, 'addr': addr}

    def lookup(self, name: str) -> dict:
        """根據變數名稱查出型別與位址"""
        if name not in self.table:
            raise Exception(f"Runtime error: Undefined variable '{name}'.")
        return self.table[name] 