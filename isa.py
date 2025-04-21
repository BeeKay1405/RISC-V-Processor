# isa.py
# RISC-V RV64IM + D ISA definitions

# ----------------------------------------------------------------------------
# OPCODES: mapping each instruction name to its 7-bit opcode field (bits [6:0])
# ----------------------------------------------------------------------------
OPCODES = {
    # U-type
    'LUI':    0b0110111,
    'AUIPC':  0b0010111,
    # J-type
    'JAL':    0b1101111,
    'JALR':   0b1100111,
    # Branch (B-type)
    'BEQ':    0b1100011,
    'BNE':    0b1100011,
    'BLT':    0b1100011,
    'BGE':    0b1100011,
    'BLTU':   0b1100011,
    'BGEU':   0b1100011,
    # Load (I-type)
    'LB':     0b0000011,
    'LH':     0b0000011,
    'LW':     0b0000011,
    'LD':     0b0000011,
    'LBU':    0b0000011,
    'LHU':    0b0000011,
    'LWU':    0b0000011,
    # Store (S-type)
    'SB':     0b0100011,
    'SH':     0b0100011,
    'SW':     0b0100011,
    'SD':     0b0100011,
    # Immediate ALU (I-type)
    'ADDI':   0b0010011,
    'SLTI':   0b0010011,
    'SLTIU':  0b0010011,
    'XORI':   0b0010011,
    'ORI':    0b0010011,
    'ANDI':   0b0010011,
    'SLLI':   0b0010011,
    'SRLI':   0b0010011,
    'SRAI':   0b0010011,
    # Register ALU (R-type)
    'ADD':    0b0110011,
    'SUB':    0b0110011,
    'SLL':    0b0110011,
    'SLT':    0b0110011,
    'SLTU':   0b0110011,
    'XOR':    0b0110011,
    'SRL':    0b0110011,
    'SRA':    0b0110011,
    'OR':     0b0110011,
    'AND':    0b0110011,
    # M-extension (same OP opcode)
    'MUL':    0b0110011,
    'MULH':   0b0110011,
    'MULHSU': 0b0110011,
    'MULHU':  0b0110011,
    'DIV':    0b0110011,
    'DIVU':   0b0110011,
    'REM':    0b0110011,
    'REMU':   0b0110011,
    # Fence/System
    'FENCE':    0b0001111,
    'FENCE.I':  0b0001111,
    'ECALL':    0b1110011,
    'EBREAK':   0b1110011,
    # F-extension D loads/stores
    'FLD':    0b0000111,
    'FSD':    0b0100111,
    # FP arithmetic/logical (OP-FP)
    'FADD.D': 0b1010011,
    'FSUB.D': 0b1010011,
    'FMUL.D': 0b1010011,
    'FDIV.D': 0b1010011,
    'FSQRT.D':0b1010011,
    'FSGNJ.D': 0b1010011,
    'FSGNJN.D':0b1010011,
    'FSGNJX.D':0b1010011,
    'FMIN.D':  0b1010011,
    'FMAX.D':  0b1010011,
    'FCVT.S.D':0b1010011,
    'FCVT.D.S':0b1010011,
    'FCVT.W.D':0b1010011,
    'FCVT.WU.D':0b1010011,
    'FCVT.D.W':0b1010011,
    'FCVT.D.WU':0b1010011,
    'FMV.X.D': 0b1010011,
    'FMV.D.X': 0b1010011,
    'FCLASS.D':0b1010011,
    # FMA-extension (R4-type)
    'FMADD.D': 0b1000011,
    'FMSUB.D': 0b1000011,
    'FNMADD.D':0b1000011,
    'FNMSUB.D':0b1000011,
}

# ----------------------------------------------------------------------------
# FUNCT3: mapping each instruction to its 3-bit funct3 field (bits [14:12])
# ----------------------------------------------------------------------------
FUNCT3 = {
    # Loads
    'LB':   0b000, 'LH':   0b001, 'LW':   0b010, 'LD':   0b011,
    'LBU':  0b100, 'LHU':  0b101, 'LWU':  0b110,
    # Stores
    'SB':   0b000, 'SH':   0b001, 'SW':   0b010, 'SD':   0b011,
    # Immediate ALU
    'ADDI': 0b000, 'SLTI': 0b010, 'SLTIU':0b011,
    'XORI': 0b100, 'ORI':  0b110, 'ANDI': 0b111,
    'SLLI': 0b001, 'SRLI': 0b101, 'SRAI': 0b101,
    # Register ALU / M-extension
    'ADD':  0b000, 'SUB':  0b000, 'SLL':  0b001,
    'SLT':  0b010, 'SLTU': 0b011, 'XOR':  0b100,
    'SRL':  0b101, 'SRA':  0b101, 'OR':   0b110,
    'AND':  0b111,
    'MUL':  0b000, 'MULH': 0b001, 'MULHSU':0b010,'MULHU':0b011,
    'DIV':  0b100, 'DIVU': 0b101, 'REM':  0b110,'REMU': 0b111,
    # Branches
    'BEQ':  0b000, 'BNE':  0b001, 'BLT':  0b100,
    'BGE':  0b101, 'BLTU': 0b110,'BGEU': 0b111,
    # JALR
    'JALR': 0b000,
    # Fence/System
    'FENCE':   0b000, 'FENCE.I':0b001,
    'ECALL':   0b000, 'EBREAK':0b000,
    # FP loads/stores
    'FLD': 0b011, 'FSD': 0b011,
    # FP arithmetic/logical (rm = rounding mode bits)
    'FADD.D': 0b000, 'FSUB.D': 0b000,
    'FMUL.D': 0b000, 'FDIV.D': 0b000,
    'FSQRT.D':0b000,
    'FSGNJ.D':0b000,'FSGNJN.D':0b000,'FSGNJX.D':0b000,
    'FMIN.D':0b000,'FMAX.D':0b000,
    'FCVT.S.D':0b000,'FCVT.D.S':0b000,
    'FCVT.W.D':0b000,'FCVT.WU.D':0b000,
    'FCVT.D.W':0b000,'FCVT.D.WU':0b000,
    'FMV.X.D':0b000,'FMV.D.X':0b000,
    'FCLASS.D':0b000,
    # FMA-extension (rm bits also in funct3)
    'FMADD.D':0b000,'FMSUB.D':0b000,'FNMADD.D':0b000,'FNMSUB.D':0b000,
}

# ----------------------------------------------------------------------------
# FUNCT7: mapping each instruction to its 7-bit funct7 field (bits [31:25])
# ----------------------------------------------------------------------------
FUNCT7 = {
    # Register ALU
    'ADD':    0b0000000, 'SUB':    0b0100000,
    'SLL':    0b0000000, 'SLT':    0b0000000,
    'SLTU':   0b0000000, 'XOR':    0b0000000,
    'SRL':    0b0000000, 'SRA':    0b0100000,
    'OR':     0b0000000, 'AND':    0b0000000,
    # Immediate shifts
    'SLLI':   0b0000000, 'SRLI':   0b0000000, 'SRAI':   0b0100000,
    # M-extension
    'MUL':    0b0000001, 'MULH':   0b0000001,
    'MULHSU': 0b0000001,'MULHU':  0b0000001,
    'DIV':    0b0000001, 'DIVU':   0b0000001,
    'REM':    0b0000001, 'REMU':   0b0000001,
    # F-extension D (OP-FP fmt=001 << 5 = 0x20 + funct5)
    'FADD.D':  0b00100000, 'FSUB.D':  0b00100001,
    'FMUL.D':  0b00100010, 'FDIV.D':  0b00100011,
    'FSQRT.D': 0b00101011,
    'FSGNJ.D': 0b00100100, 'FSGNJN.D':0b00100101, 'FSGNJX.D':0b00100110,
    'FMIN.D':  0b00100111, 'FMAX.D':  0b00101000,
    'FCVT.S.D':0b00110000, 'FCVT.D.S':0b00110001,
    'FCVT.W.D':0b00111000, 'FCVT.WU.D':0b00111001,
    'FCVT.D.W':0b00111010, 'FCVT.D.WU':0b00111011,
    'FMV.X.D': 0b00111100, 'FMV.D.X': 0b00111101,
    'FCLASS.D':0b00111110,
    # FMA-extension
    # fmt=001 <<5 =0x20, plus funct5 codes:
    'FMADD.D': 0b00100000, 'FMSUB.D': 0b00100001,
    'FNMADD.D':0b00100011, 'FNMSUB.D':0b00100010,
}
