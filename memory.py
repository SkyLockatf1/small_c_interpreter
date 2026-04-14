class VirtualMemory:
    def __init__(self, size=65536):  # 預設 64KB 的空間 [cite: 7]
        # 使用 bytearray 模擬連續位址空間
        self.mem = bytearray(size)
        self.size = size
        self.global_top = 0      # 全域區目前用到的最高位址 從左邊往右加
        self.stack_top = size    # 區域堆疊目前用到的最低位址 從右邊往左加

        self.allocations = {}    # 紀錄array長度 key:陣列指針地址 value:長度


    # ======int======  
    def set_int(self, addr, value):
        # 給地址和值存int
        if addr + 4 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        # 使用小端序 (Little-endian) 轉換為 4 bytes
        # 例如: 0x12345678 會存成 [0x78, 0x56, 0x34, 0x12]
        bytes_val = value.to_bytes(4, 'little', signed=True)
        self.mem[addr:addr+4] = bytes_val
    
    def get_int(self, addr):
        # 給地址取int
        if addr + 4 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
            
        bytes_val = self.mem[addr:addr+4]
        return int.from_bytes(bytes_val, 'little', signed=True)
    

    # ======char======  
    def set_char(self, addr, value):
        # 給地址和8 bit字元存char
        if addr + 1 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
            
        # value 可以是單個字元 'A' 或整數 65
        if isinstance(value, str):
            val = ord(value) #轉成ASCII
        else:
            val = value
            
        # 確保在 -128 到 127 範圍內 [cite: 14]
        self.mem[addr] = val & 0xFF #確保只有8 bit

    def get_char(self, addr):
        # 給地址取字元
        if addr + 1 > self.size:
            raise RuntimeError("Memory Access Violation: Out of bounds")
        
        val = self.mem[addr]
        # 處理有號數轉換 (8-bit)
        if val > 127:
            val -= 256
        return val
    


    def alloc_global(self, size):
        #分配全域空間
        addr = self.global_top
        self.global_top += size
        if self.global_top >= self.stack_top:
            raise RuntimeError("Runtime error: out of memory (Stack-Heap collision)")
        self.allocations[addr] = size
        return addr
    
    def alloc_stack(self, size):
        #分配全域空間
        addr = self.stack_top
        self.stack_top -= size
        if self.global_top >= self.stack_top:
            raise RuntimeError("Runtime error: out of memory (Stack Overflow)")
        self.allocations[addr] = size
        return addr
    
    def free_stack(self, size):
        # 函式結束 回收記憶體
        self.stack_ptr += size





    def set_string(self, string_content): # char array
        """
        處理字串常數：
        1. 處理跳脫字元 (如 \n, \t) 
        2. 分配空間並寫入 mem
        3. 自動附加 \0 
        4. 回傳字串在記憶體中的起始位址
        """
        def _process_escape_sequences(s):
            # 轉換跳脫字符成ascii
            s = s.replace('\\n', '\n').replace('\\t', '\t').replace('\\0', '\0')
            s = s.replace('\\\\', '\\').replace("\\'", "'").replace('\\"', '"')
            return s.encode('ascii')
        

        # 處理跳脫字符
        processed_bytes = _process_escape_sequences(string_content)
        

        start_addr = self.global_top
        size_needed = len(processed_bytes) + 1
        
        if start_addr + size_needed >= self.size:
            raise RuntimeError("Runtime error: memory overflow while allocating string")

        # 寫入字串內容
        self.mem[start_addr:start_addr + len(processed_bytes)] = processed_bytes

        self.allocations[start_addr] = size_needed
        
        # 寫入結尾空字元 \0 (ASCII 0) [cite: 19, 20]
        self.mem[start_addr + len(processed_bytes)] = 0
        
        # 更新全域指標，確保下一個變數不會覆蓋字串
        self.global_top += size_needed
        
        return start_addr
    
    
    def calc_ptr_offset(self, base_addr, target_type, offset_count):
        """
        根據型別計算指標偏移後的位址
        :param base_addr: 目前指標存儲的位址值 (int)
        :param target_type: 指標指向的型別 ('int' 或 'char')
        :param offset_count: 加減的數量 (例如 p + 1 的 1)
        """
        # 根據型別決定步長 (Stride)
        if target_type == 'int':
            stride = 4  # int 寬度為 4 
        elif target_type == 'char':
            stride = 1  # char 寬度為 1 
        else:
            raise RuntimeError(f"Runtime error: Unsupported pointer type {target_type}")

        # 計算新位址
        new_addr = base_addr + (offset_count * stride)

        # 邊界檢查 (加分項目建議) [cite: 862]
        if new_addr < 0 or new_addr >= self.size:
            raise RuntimeError(f"Runtime error: Pointer arithmetic out of bounds ({new_addr})")
        self.check_bounds(base_addr, new_addr, stride)

        return new_addr
    

    def check_bounds(self, base_addr, target_addr, element_size):    # 確認陣列邊界
        """
        base_addr: 陣列的起始位址 (從符號表取得)
        target_addr: 加上 offset 後想要存取的目標位址
        element_size: 型別大小 (int=4, char=1)
        """
        if base_addr not in self.allocations:
            # 如果找不到分配記錄，可能是一個非法指標
            raise RuntimeError(f"Runtime error: invalid memory access at {target_addr}")
        
        max_size = self.allocations[base_addr]
        
        # 檢查目標位址加上資料寬度，是否超過了當初分配的大小
        if target_addr < base_addr or (target_addr + element_size) > (base_addr + max_size):
            # 報錯
            index = (target_addr - base_addr) // element_size
            size = max_size // element_size
            raise RuntimeError(f"Runtime error: array index out of bounds (index {index}, size {size}).")
    
    def reset(self, size=65536):
        self.mem = bytearray(size)
        self.size = size
        self.global_top = 0      # 全域區目前用到的最高位址 從左邊往右加
        self.stack_top = size  
        self.allocations = {}
        # 估計還要清空symtable
    
