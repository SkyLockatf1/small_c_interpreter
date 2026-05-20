# Stride lookup，鏡像 symtable.sizeof_type，避免 memory.py 反向 import symtable
# 導致潛在循環 import 問題。
_SIZEOF = {'int': 4, 'char': 1, 'int*': 4, 'char*': 4}

def _sizeof_type(var_type: str) -> int:
    if var_type not in _SIZEOF:
        raise RuntimeError(f"Runtime error: Unsupported type '{var_type}'")
    return _SIZEOF[var_type]


class VirtualMemory:
    def __init__(self, size=65536):
        # 使用 bytearray 模擬 64KB 連續位址空間
        self.mem = bytearray(size)
        self.size = size
        self.global_top = 0      # 全域區目前用到的最高位址，從左往右增長
        self.stack_top = size    # 堆疊區目前用到的最低位址，從右往左縮減
        self.allocations = {}    # addr -> size，記錄所有活躍的 allocation

    # ── int 讀寫 ──────────────────────────────────────────────────────────────

    def set_int(self, addr: int, value: int):
        """寫入 32-bit signed int（小端序）。超出範圍時截斷，不丟 OverflowError。"""
        if addr + 4 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        # 32-bit signed wrap-around：(value + 2^31) % 2^32 - 2^31
        value = (value + 2**31) % 2**32 - 2**31
        self.mem[addr:addr+4] = value.to_bytes(4, 'little', signed=True)

    def get_int(self, addr: int) -> int:
        """讀取 32-bit signed int（小端序）。"""
        if addr + 4 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        return int.from_bytes(self.mem[addr:addr+4], 'little', signed=True)

    # ── char 讀寫 ─────────────────────────────────────────────────────────────

    def set_char(self, addr: int, value):
        """寫入 8-bit char，接受整數或單字元字串，自動截斷為低 8 位元。"""
        if addr + 1 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        if isinstance(value, str):
            value = ord(value)
        self.mem[addr] = value & 0xFF

    def get_char(self, addr: int) -> int:
        """讀取 8-bit char，回傳有號整數（-128 ~ 127）。"""
        if addr + 1 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        val = self.mem[addr]
        return val - 256 if val > 127 else val

    # ── 統一讀寫入口 ──────────────────────────────────────────────────────────

    def read(self, addr: int, var_type: str) -> int:
        """依型別讀取：'int' 呼叫 get_int，'char' 呼叫 get_char。"""
        if var_type == 'int':
            return self.get_int(addr)
        if var_type == 'char':
            return self.get_char(addr)
        raise RuntimeError(f"Runtime error: read() unsupported type '{var_type}'")

    def write(self, addr: int, var_type: str, value: int):
        """依型別寫入：'int' 呼叫 set_int，'char' 呼叫 set_char。"""
        if var_type == 'int':
            self.set_int(addr, value)
        elif var_type == 'char':
            self.set_char(addr, value)
        else:
            raise RuntimeError(f"Runtime error: write() unsupported type '{var_type}'")

    # ── 指標讀寫（4-byte unsigned，int* / char* 統一格式）────────────────────

    def get_ptr(self, addr: int) -> int:
        """讀取儲存在 addr 的指標值（4-byte unsigned little-endian）。"""
        if addr + 4 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        return int.from_bytes(self.mem[addr:addr+4], 'little', signed=False)

    def set_ptr(self, addr: int, ptr_val: int):
        """寫入指標值到 addr（4-byte unsigned little-endian）。"""
        if addr + 4 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        if ptr_val < 0:
            raise RuntimeError("Runtime error: Pointer value cannot be negative")
        self.mem[addr:addr+4] = ptr_val.to_bytes(4, 'little', signed=False)

    # ── 配置 ──────────────────────────────────────────────────────────────────

    def alloc_global(self, size: int) -> int:
        """在全域區（左側）分配 size bytes，回傳起始位址。"""
        addr = self.global_top
        self.global_top += size
        if self.global_top >= self.stack_top:
            raise RuntimeError("Runtime error: out of memory (Stack-Heap collision)")
        self.allocations[addr] = size
        return addr

    def alloc_stack(self, size: int) -> int:
        """在堆疊區（右側）分配 size bytes，回傳起始位址。

        修正 off-by-one：先減再取 addr。
          舊版：addr = stack_top (65536) → set_int(65536) 超出 bytearray 範圍
          新版：stack_top -= size → addr = stack_top (65532) → 合法
        """
        self.stack_top -= size
        if self.global_top >= self.stack_top:
            raise RuntimeError("Runtime error: out of memory (Stack Overflow)")
        addr = self.stack_top
        self.allocations[addr] = size
        return addr

    def free_stack_frame(self, frame_entry_top: int):
        """釋放函式進入後的所有 stack allocation，並恢復 stack_top。

        frame_entry_top：呼叫函式「前」記錄的 stack_top 值。
        Interpreter 只需在函式進入時記住 stack_top，不需要計算 frame_size。
        """
        to_remove = [a for a in self.allocations
                     if self.stack_top <= a < frame_entry_top]
        for a in to_remove:
            del self.allocations[a]
        self.stack_top = frame_entry_top

    # ── 陣列元素存取（含邊界檢查）────────────────────────────────────────────

    def array_read(self, base_addr: int, index: int, elem_type: str) -> int:
        """讀取 base_addr[index]，含邊界檢查。對應 C 的 arr[i]。"""
        stride = _sizeof_type(elem_type)
        target = base_addr + index * stride
        self.check_bounds(base_addr, target, stride)
        return self.read(target, elem_type)

    def array_write(self, base_addr: int, index: int, elem_type: str, value: int):
        """寫入 base_addr[index] = value，含邊界檢查。對應 C 的 arr[i] = v。"""
        stride = _sizeof_type(elem_type)
        target = base_addr + index * stride
        self.check_bounds(base_addr, target, stride)
        self.write(target, elem_type, value)

    # ── 指標算術 ──────────────────────────────────────────────────────────────

    def ptr_add(self, ptr_val: int, offset: int, elem_type: str) -> int:
        """計算 ptr_val + offset * stride，對應 C 的 p + n 或 p - n（offset 可為負）。

        stride 由 _sizeof_type(elem_type) 決定，支援 'int'/'char'/'int*'/'char*'。
        只驗證結果在合法記憶體範圍內，不強制在同一 allocation 內。
        """
        stride = _sizeof_type(elem_type)
        new_addr = ptr_val + offset * stride
        if new_addr < 0 or new_addr >= self.size:
            raise RuntimeError(
                f"Runtime error: Pointer arithmetic out of bounds ({new_addr})"
            )
        return new_addr

    # ── 邊界檢查 ──────────────────────────────────────────────────────────────

    def find_allocation(self, addr: int):
        """找出包含 addr 的 allocation，回傳 (base_addr, size) 或 None。

        支援任意中間位址，例如 p = &arr[3]，仍能找到 arr 的 allocation。
        時間複雜度 O(n)，n = 目前活躍的 allocation 數量。
        """
        for base, size in self.allocations.items():
            if base <= addr < base + size:
                return (base, size)
        return None

    def check_ptr(self, addr: int, access_size: int):
        """確認 [addr, addr+access_size) 落在某個有效的 allocation 內。

        比 check_bounds 更方便：呼叫方不需要知道 base_addr，
        find_allocation 會自動從任意地址找到所屬的 allocation。
        """
        result = self.find_allocation(addr)
        if result is None:
            raise RuntimeError(
                f"Runtime error: invalid memory access at {addr:#x}"
            )
        base, size = result
        if addr + access_size > base + size:
            raise RuntimeError(
                f"Runtime error: memory access at {addr:#x} size {access_size} "
                f"exceeds allocation [{base:#x}, {base + size:#x})"
            )

    def check_bounds(self, base_addr: int, target_addr: int, element_size: int):
        """舊 API 保留（向下相容）。確認陣列元素存取不超出 allocation 範圍。

        base_addr 必須是 allocation 的起始位址（allocations dict 的 key）。
        """
        if base_addr not in self.allocations:
            raise RuntimeError(
                f"Runtime error: invalid memory access at {target_addr}"
            )
        max_size = self.allocations[base_addr]
        if target_addr < base_addr or (target_addr + element_size) > (base_addr + max_size):
            index = (target_addr - base_addr) // element_size
            size = max_size // element_size
            raise RuntimeError(
                f"Runtime error: array index out of bounds (index {index}, size {size})."
            )

    # ── 字串輔助 ──────────────────────────────────────────────────────────────

    def read_cstring(self, addr: int, max_len: int = 4096) -> str:
        """從 addr 讀取 C 字串（讀到 \\0 為止），回傳 Python str。

        優先以 find_allocation 找到所屬 allocation 的邊界作為上限，
        防止讀入相鄰 allocation 的資料。找不到時才用 max_len 作為保護上限。
        """
        if addr < 0 or addr >= self.size:
            raise RuntimeError(f"Runtime error: invalid string address {addr:#x}")

        result = self.find_allocation(addr)
        if result is not None:
            base, size = result
            limit = base + size
        else:
            limit = min(addr + max_len, self.size)

        chars = []
        pos = addr
        while pos < limit:
            c = self.mem[pos]
            if c == 0:
                break
            chars.append(chr(c))
            pos += 1
        else:
            # while 條件耗盡（到達 limit）仍未找到 \0：字串未正確終止
            raise RuntimeError(
                f"Runtime error: unterminated string starting at {addr:#x}"
            )
        return ''.join(chars)

    def write_cstring(self, addr: int, s: str, max_len: int):
        """將字串 s + \\0 寫入 addr，total 不超過 max_len bytes。

        供 scanf("%s")、strcpy、strcat、itoa 使用。
        """
        encoded = s.encode('ascii')
        needed = len(encoded) + 1  # 含結尾 \0
        if needed > max_len:
            raise RuntimeError(
                f"Runtime error: buffer overflow: string length {len(encoded)} "
                f"exceeds buffer size {max_len - 1}"
            )
        self.check_ptr(addr, needed)
        self.mem[addr:addr + len(encoded)] = encoded
        self.mem[addr + len(encoded)] = 0

    def alloc_string(self, string_content: str) -> int:
        """分配全域空間並寫入字串常數（含 \\0），回傳起始位址。

        字串字面量具有靜態儲存期（C static storage duration），
        永遠分配在全域區，不受目前 scope level 影響。
        """
        encoded = string_content.encode('ascii')
        size_needed = len(encoded) + 1
        addr = self.global_top

        if addr + size_needed > self.size:
            raise RuntimeError("Runtime error: memory overflow while allocating string")

        self.mem[addr:addr + len(encoded)] = encoded
        self.mem[addr + len(encoded)] = 0
        self.allocations[addr] = size_needed
        self.global_top += size_needed
        return addr

    def set_string(self, string_content: str) -> int:
        """舊名保留為 alias（向下相容），實作委派給 alloc_string。"""
        return self.alloc_string(string_content)

    # ── 重置 ──────────────────────────────────────────────────────────────────

    def reset(self, size=65536):
        """清空記憶體與所有配置紀錄，供 NEW 指令重置執行環境時使用。"""
        self.mem = bytearray(size)
        self.size = size
        self.global_top = 0
        self.stack_top = size
        self.allocations = {}
