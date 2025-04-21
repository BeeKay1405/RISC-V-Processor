from register_file import RegisterFile, FloatRegisterFile
from pipeline import IF_ID, ID_EX, EX_MEM, MEM_WB
from control_unit import decode_instruction
from execute_stage import execute_stage
from alu import alu_operation
from utils import get_bits, sign_extend
from hazard_unit import HazardUnit

# Instruction memory (hardcoded)
instruction_memory = {
    0: 0x00000513,  # addi x10, x0, 0
    4: 0x00100593,  # addi x11, x0, 1
    8: 0x00b50633,  # add x12, x10, x11
    12: 0x00c000ef,  # jal x1, +12 (simulate control hazard)
    16: 0x00000000
}

data_memory = {}

# Pipeline registers
if_id = IF_ID()
id_ex = ID_EX()
ex_mem = EX_MEM()
mem_wb = MEM_WB()

# Register files
reg_file = RegisterFile()
fp_reg_file = FloatRegisterFile()

# PC and cycle
pc = 0
cycle = 0

done = False
hazard_unit = HazardUnit()
stall = False
flush = False

print("Cycle-by-cycle simulation\n")

while not done and cycle < 20:
    print(f"Cycle {cycle}:")

    # WB stage
    rd = mem_wb.get("rd")
    if mem_wb.get("reg_write") and rd is not None:
        val = mem_wb["mem_data"] if mem_wb.get("mem_to_reg") else mem_wb["alu_result"]
        if mem_wb.get("float_write"):
            fp_reg_file.write(rd, val)
        else:
            reg_file.write(rd, val)

    # MEM stage
    mem_wb.clear()
    mem_wb.update({
        "rd": ex_mem.get("rd"),
        "reg_write": ex_mem.get("reg_write"),
        "mem_to_reg": ex_mem.get("mem_to_reg"),
        "alu_result": ex_mem.get("alu_result"),
        "fp_op": ex_mem.get("fp_op", False),
        "float_write": ex_mem.get("float_write", False),
    })

    addr = ex_mem.get("alu_result")
    rs2_val = ex_mem.get("rs2_val")
    opcode = ex_mem.get("opcode")

    if opcode in ["lw", "ld", "flw", "fld"]:
        mem_wb["mem_data"] = data_memory.get(addr, 0)
    elif opcode in ["sw", "sd", "fsw", "fsd"]:
        data_memory[addr] = rs2_val
        mem_wb["mem_data"] = None
    else:
        mem_wb["mem_data"] = None

    # EX stage
    execute_stage(id_ex, ex_mem, reg_file, fp_reg_file)

    # ID stage
    if not stall:
        id_ex.clear()
        instr = if_id.get("instr")
        if instr is not None:
            decoded = decode_instruction(instr)
            id_ex.update(decoded)
            id_ex["rs1_val"], id_ex["rs2_val"] = reg_file.read(decoded["rs1"], decoded["rs2"])

            # Check for control hazard
            if decoded["opcode"] in ["jal", "jalr", "beq", "bne", "blt", "bge"]:
                flush = True

            # Detect load-use hazard
            if hazard_unit.detect_load_use_hazard(id_ex, ex_mem):
                stall = True

    else:
        # Insert bubble
        id_ex.clear()
        stall = False

    # IF stage
    if not stall:
        instr = instruction_memory.get(pc, 0)
        if_id.clear()
        if_id.update({"instr": instr, "pc": pc})
        pc += 4
    else:
        # Hold IF/ID during stall
        pass

    if flush:
        if_id.clear()
        id_ex.clear()
        flush = False

    print(f"\tIF: PC={if_id.get('pc')}, Instr={hex(if_id.get('instr', 0))}")
    print(f"\tID: {id_ex}")
    print(f"\tEX: {ex_mem}")
    print(f"\tMEM: {mem_wb}")

    if pc >= max(instruction_memory.keys()):
        done = True

    cycle += 1

print("\nFinal Register File:")
reg_file.dump()
