from control_unit import get_control_signals
from alu import alu
from isa_utils import get_immediate  # from your Phase 2
from register_file import RegisterFile

def execute(decoded_inst, reg_file):
    # Decoded instruction has: mnemonic, rs1, rs2, rd, opcode, funct3, funct7
    signals = get_control_signals(decoded_inst.mnemonic)
    rs1_val, rs2_val = reg_file.read(decoded_inst.rs1, decoded_inst.rs2)
    imm = get_immediate(decoded_inst)

    op2 = imm if signals['aluSrc'] else rs2_val
    alu_result = alu(rs1_val, op2, signals['aluOp'])

    return {
        'alu_result': alu_result,
        'write_back': signals['regWrite'],
        'rd': decoded_inst.rd,
        'write_data': alu_result,
        'mem_read': signals['memRead'],
        'mem_write': signals['memWrite'],
        'mem_to_reg': signals['memToReg'],
        'branch': signals['branch'],
    }
