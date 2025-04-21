class RegisterFile:
    def __init__(self):
        # Integer registers x0–x31 (64-bit)
        self.regs = [0] * 32
        # Floating-point registers f0–f31 (64-bit)
        self.fregs = [0.0] * 32
        # Floating-Point Control and Status Register (32-bit)
        self.fcsr = 0

    # Integer register read
    def read(self, rs1, rs2):
        return self.regs[rs1], self.regs[rs2]

    def read1(self, rs1):
        return self.regs[rs1]

    # Integer register write
    def write(self, rd, value):
        if rd != 0:
            self.regs[rd] = value

    # Floating-point register read
    def fread(self, frs1, frs2):
        return self.fregs[frs1], self.fregs[frs2]

    def fread1(self, frs1):
        return self.fregs[frs1]

    # Floating-point register write
    def fwrite(self, frd, value):
        if frd != 0:
            self.fregs[frd] = value

    # FCSR access
    def get_fcsr(self):
        return self.fcsr

    def set_fcsr(self, value):
        self.fcsr = value & 0xFFFFFFFF  # mask to 32 bits

    # Dump all registers
    def dump(self):
        print("Integer Registers:")
        for i in range(0, 32, 4):
            print(f"x{i}: {self.regs[i]:#x}\tx{i+1}: {self.regs[i+1]:#x}\tx{i+2}: {self.regs[i+2]:#x}\tx{i+3}: {self.regs[i+3]:#x}")
        
        print("\nFloating-Point Registers:")
        for i in range(0, 32, 4):
            print(f"f{i}: {self.fregs[i]:.6f}\tf{i+1}: {self.fregs[i+1]:.6f}\tf{i+2}: {self.fregs[i+2]:.6f}\tf{i+3}: {self.fregs[i+3]:.6f}")

        print(f"\nFCSR: 0x{self.fcsr:08x}")
