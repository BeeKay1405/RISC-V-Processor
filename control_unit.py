def get_control_signals(mnemonic):
    signals = {
        'regWrite': 0,
        'aluSrc': 0,
        'memRead': 0,
        'memWrite': 0,
        'memToReg': 0,
        'branch': 0,
        'aluOp': 'NOP'
    }

    if mnemonic in ['add', 'sub', 'mul', 'and', 'or', 'xor', 'sll', 'srl', 'sra', 'slt', 'sltu']:
        signals.update({'regWrite': 1, 'aluSrc': 0, 'aluOp': mnemonic})
    elif mnemonic in ['addi', 'andi', 'ori', 'xori', 'slli', 'srli', 'srai', 'slti', 'sltiu']:
        signals.update({'regWrite': 1, 'aluSrc': 1, 'aluOp': mnemonic[:-1]})
    elif mnemonic == 'lw':
        signals.update({'regWrite': 1, 'aluSrc': 1, 'memRead': 1, 'memToReg': 1, 'aluOp': 'add'})
    elif mnemonic == 'sw':
        signals.update({'aluSrc': 1, 'memWrite': 1, 'aluOp': 'add'})
    elif mnemonic in ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']:
        signals.update({'branch': 1, 'aluOp': mnemonic})
    elif mnemonic == 'jal' or mnemonic == 'jalr':
        signals.update({'regWrite': 1, 'aluSrc': 1, 'aluOp': 'add'})
    return signals
