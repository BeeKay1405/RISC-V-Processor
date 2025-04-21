# alu.py
# RV64I + M-extension ALU implementation

MASK64 = (1 << 64) - 1


def alu(op1, op2, alu_op):
    op1_u = op1 & MASK64
    op2_u = op2 & MASK64

    if alu_op == 'add':   return (op1 + op2) & MASK64
    if alu_op == 'sub':   return (op1 - op2) & MASK64
    if alu_op == 'mul':   return (op1 * op2) & MASK64
    if alu_op == 'mulh':  return ((op1 * op2) >> 64) & MASK64
    if alu_op == 'mulhu': return ((op1_u * op2_u) >> 64) & MASK64
    if alu_op == 'mulhsu': return ((op1 * op2_u) >> 64) & MASK64

    if alu_op == 'div':
        if op2 == 0:
            return -1 & MASK64
        if op1 == -2 ** 63 and op2 == -1:
            return op1  # overflow case
        return int(op1 // op2) & MASK64

    if alu_op == 'divu':
        return (op1_u // op2_u) & MASK64 if op2 != 0 else MASK64

    if alu_op == 'rem':
        if op2 == 0:
            return op1 & MASK64
        if op1 == -2 ** 63 and op2 == -1:
            return 0
        return (op1 % op2) & MASK64

    if alu_op == 'remu':
        return (op1_u % op2_u) & MASK64 if op2 != 0 else op1_u

    if alu_op == 'and':   return (op1 & op2) & MASK64
    if alu_op == 'or':    return (op1 | op2) & MASK64
    if alu_op == 'xor':   return (op1 ^ op2) & MASK64

    if alu_op == 'sll':   return (op1 << (op2 & 0x3F)) & MASK64
    if alu_op == 'srl':   return (op1_u >> (op2 & 0x3F)) & MASK64
    if alu_op == 'sra':   return (op1 >> (op2 & 0x3F)) & MASK64

    if alu_op == 'slt':   return int(op1 < op2)
    if alu_op == 'sltu':  return int(op1_u < op2_u)

    return 0
