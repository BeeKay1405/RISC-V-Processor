def get_control_signals(mnemonic):
    signals = {
        'regWrite': 0,
        'aluSrc': 0,
        'memRead': 0,
        'memWrite': 0,
        'memToReg': 0,
        'branch': 0,
        'aluOp': 'NOP',
        'fpu': 0,
        'fpuOp': None
    }

    # RV64I - R-type
    if mnemonic in ['add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and']:
        signals.update({'regWrite': 1, 'aluSrc': 0, 'aluOp': mnemonic})

    # RV64I - I-type
    elif mnemonic in ['addi', 'slti', 'sltiu', 'xori', 'ori', 'andi']:
        signals.update({'regWrite': 1, 'aluSrc': 1, 'aluOp': mnemonic[:-1]})
    elif mnemonic in ['slli', 'srli', 'srai']:
        signals.update({'regWrite': 1, 'aluSrc': 1, 'aluOp': mnemonic[:-1]})

    # Load / Store
    elif mnemonic == 'lw':
        signals.update({'regWrite': 1, 'memRead': 1, 'memToReg': 1, 'aluSrc': 1, 'aluOp': 'add'})
    elif mnemonic == 'sw':
        signals.update({'memWrite': 1, 'aluSrc': 1, 'aluOp': 'add'})

    # Branch
    elif mnemonic in ['beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu']:
        signals.update({'branch': 1, 'aluOp': mnemonic})

    # Jump
    elif mnemonic in ['jal', 'jalr']:
        signals.update({'regWrite': 1, 'aluSrc': 1, 'aluOp': 'add'})

    # M-extension
    elif mnemonic in ['mul', 'div', 'divu', 'rem', 'remu', 'mulh', 'mulhu', 'mulhsu']:
        signals.update({'regWrite': 1, 'aluSrc': 0, 'aluOp': mnemonic})

    # D-extension
    elif mnemonic == 'fld':
        signals.update({'regWrite': 1, 'memRead': 1, 'memToReg': 1, 'aluSrc': 1, 'aluOp': 'add', 'fpu': 1})
    elif mnemonic == 'fsd':
        signals.update({'memWrite': 1, 'aluSrc': 1, 'aluOp': 'add', 'fpu': 1})
    elif mnemonic in ['fadd.d', 'fsub.d', 'fmul.d', 'fdiv.d', 'fsqrt.d', 'fmax.d', 'fmin.d', 'fsgnj.d', 'fsgnjn.d', 'fsgnjx.d', 'fclass.d',
                      'fmv.x.d', 'fmv.d.x', 'fcvt.d.s', 'fcvt.s.d', 'fcvt.w.d', 'fcvt.d.w', 'fcvt.wu.d', 'fcvt.d.wu']:
        signals.update({'regWrite': 1, 'fpu': 1, 'fpuOp': mnemonic})

    return signals