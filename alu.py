def alu(op1, op2, alu_op):
    if alu_op == 'add': return op1 + op2
    if alu_op == 'sub': return op1 - op2
    if alu_op == 'mul': return op1 * op2
    if alu_op == 'and': return op1 & op2
    if alu_op == 'or':  return op1 | op2
    if alu_op == 'xor': return op1 ^ op2
    if alu_op == 'sll': return op1 << (op2 & 0x3F)
    if alu_op == 'srl': return (op1 % (1 << 64)) >> (op2 & 0x3F)
    if alu_op == 'sra': return op1 >> (op2 & 0x3F)
    if alu_op == 'slt': return int(op1 < op2)
    if alu_op == 'sltu': return int((op1 % (1 << 64)) < (op2 % (1 << 64)))
    return 0
