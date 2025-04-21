class RegisterFile:
    def __init__(self):
        self.regs = [0] * 32

    def read(self, rs1, rs2):
        return self.regs[rs1], self.regs[rs2]

    def write(self, rd, value):
        if rd != 0:
            self.regs[rd] = value

    def dump(self):
        for i in range(0, 32, 4):
            print(f"x{i}: {self.regs[i]:#x}\tx{i+1}: {self.regs[i+1]:#x}\tx{i+2}: {self.regs[i+2]:#x}\tx{i+3}: {self.regs[i+3]:#x}")
