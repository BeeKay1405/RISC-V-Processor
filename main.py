# main.py
import sys
from collections import namedtuple

# Assuming your files are in the same directory or accessible via PYTHONPATH
from register_file import RegisterFile #
from utils import decodeInstruction, fieldsGen, imm_i, imm_s, imm_b, imm_u, imm_j #
from alu import alu #
from control_unit import get_control_signals #
# Note: pipeline.py provided mem_stage and wb_stage, but we need distinct
# functions for each pipeline stage's logic within the main loop.
# We'll adapt the logic from pipeline.py and execute_stage.py here.

# --- Constants ---
MEM_SIZE = 1024 * 1024  # Example memory size (1MB)
NOP_INSTRUCTION = 0x00000013 # Represents `addi x0, x0, 0` (a NOP)

# --- Data Structures ---
Instruction = namedtuple("Instruction", ["inst_word", "mnemonic", "fields"])

# Pipeline Registers (dictionaries to hold state between stages)
if_id_reg = {'pc': 0, 'inst_word': NOP_INSTRUCTION}
id_ex_reg = {'pc': 0, 'inst_word': NOP_INSTRUCTION, 'ctrl': {}, 'rs1_val': 0, 'rs2_val': 0, 'imm': 0, 'rd': 0, 'rs1': 0, 'rs2': 0, 'mnemonic': 'nop'}
ex_mem_reg = {'pc': 0, 'inst_word': NOP_INSTRUCTION, 'ctrl': {}, 'alu_result': 0, 'rs2_val': 0, 'rd': 0, 'branch_target': 0, 'branch_taken': False, 'mnemonic': 'nop'}
mem_wb_reg = {'pc': 0, 'inst_word': NOP_INSTRUCTION, 'ctrl': {}, 'mem_data': 0, 'alu_result': 0, 'rd': 0, 'mnemonic': 'nop'}

# --- Components ---
pc = 0
register_file = RegisterFile() #
# Simple dictionary-based memory for instructions and data
memory = {} # Start empty, load program later

# --- Hazard Detection Unit ---
class HazardUnit:
    def __init__(self):
        self.stall_if = False
        self.stall_id = False
        self.stall_ex = False
        self.flush_if_id = False
        self.flush_id_ex = False
        self.forward_a_ex = 0 # 0: no forward, 1: from EX/MEM.alu_result, 2: from MEM/WB.result
        self.forward_b_ex = 0 # 0: no forward, 1: from EX/MEM.alu_result, 2: from MEM/WB.result

    def detect_and_resolve(self, id_ex, ex_mem, mem_wb):
        """Detects hazards and sets stall/flush/forward signals."""
        self.stall_if = False
        self.stall_id = False
        self.stall_ex = False
        self.flush_if_id = False
        self.flush_id_ex = False
        self.forward_a_ex = 0
        self.forward_b_ex = 0

        id_rs1 = id_ex.get('rs1', 0)
        id_rs2 = id_ex.get('rs2', 0)
        ex_rd = ex_mem.get('rd', 0)
        ex_ctrl = ex_mem.get('ctrl', {})

        # --- 1. EX Hazard (Load-Use Hazard) ---
        if ex_ctrl.get('memRead', 0) and ex_rd != 0 and (ex_rd == id_rs1 or ex_rd == id_rs2):
            print(f"Hazard: Load-Use detected! Stalling IF/ID/EX. (EX.rd={ex_rd}, ID.rs1={id_rs1}, ID.rs2={id_rs2})")
            self.stall_if = True
            self.stall_id = True
            self.stall_ex = True
            self.flush_id_ex = True # Insert NOP into EX
            return # Stall overrides forwarding for load-use

        # --- 2. Data Forwarding ---
        mem_rd = mem_wb.get('rd', 0)
        mem_ctrl = mem_wb.get('ctrl', {})
        wb_reg_write = mem_ctrl.get('regWrite', 0)

        ex_reg_write = ex_ctrl.get('regWrite', 0)

        # Forward from EX/MEM stage
        if ex_reg_write and ex_rd != 0:
            if ex_rd == id_rs1:
                self.forward_a_ex = 1
                print(f"Hazard: Forwarding A from EX/MEM (EX.rd={ex_rd} == ID.rs1)")
            if ex_rd == id_rs2:
                self.forward_b_ex = 1
                print(f"Hazard: Forwarding B from EX/MEM (EX.rd={ex_rd} == ID.rs2)")

        # Forward from MEM/WB stage (overrides EX/MEM if needed for same register)
        if wb_reg_write and mem_rd != 0:
            # Check if EX stage didn't already forward for this register
            if not (ex_reg_write and ex_rd != 0 and ex_rd == id_rs1):
                 if mem_rd == id_rs1:
                    self.forward_a_ex = 2
                    print(f"Hazard: Forwarding A from MEM/WB (MEM.rd={mem_rd} == ID.rs1)")
            if not (ex_reg_write and ex_rd != 0 and ex_rd == id_rs2):
                if mem_rd == id_rs2:
                    self.forward_b_ex = 2
                    print(f"Hazard: Forwarding B from MEM/WB (MEM.rd={mem_rd} == ID.rs2)")

        # --- 3. Control Hazards (Branches/Jumps in EX stage) ---
        # Simple approach: Assume branch not taken, flush if wrong.
        if ex_mem.get('branch_taken'):
            print(f"Hazard: Branch/Jump Taken in EX stage. Flushing IF/ID and ID/EX.")
            self.flush_if_id = True
            self.flush_id_ex = True

hazard_unit = HazardUnit()

# --- Pipeline Stages ---

def fetch(current_pc):
    """Fetch instruction from memory based on PC."""
    if current_pc not in memory:
        # print(f"Warning: PC {current_pc:#x} not in instruction memory. Fetching NOP.")
        inst_word = NOP_INSTRUCTION
    else:
        inst_word = memory[current_pc]
    return {'pc': current_pc, 'inst_word': inst_word}

def decode(if_id_data):
    """Decode instruction, read registers."""
    inst_word = if_id_data['inst_word']
    pc = if_id_data['pc']

    if inst_word == NOP_INSTRUCTION:
         return {'pc': pc, 'inst_word': inst_word, 'ctrl': get_control_signals('nop'), 'rs1_val': 0, 'rs2_val': 0, 'imm': 0, 'rd': 0, 'rs1': 0, 'rs2': 0, 'mnemonic': 'nop'} #

    try:
        fields = fieldsGen(inst_word) #
        mnemonic = decodeInstruction(inst_word) #
    except Exception as e:
        print(f"Decode Error: Failed on word {inst_word:#010x}. {e}")
        mnemonic = "unknown"
        fields = {}

    if mnemonic == 'UNKNOWN':
        print(f"Warning: Unknown instruction {inst_word:#010x} at PC {pc:#x}. Treating as NOP.")
        mnemonic = 'nop'
        ctrl = get_control_signals('nop') #
        rs1, rs2, rd = 0, 0, 0
        imm = 0
    else:
        ctrl = get_control_signals(mnemonic) #
        rs1 = fields.get('rs1', 0)
        rs2 = fields.get('rs2', 0)
        rd = fields.get('rd', 0)

        opc = fields.get('opcode', 0)
        imm = 0
        if ctrl['aluSrc'] == 1:
             # Determine immediate type based on mnemonic/opcode
             if mnemonic.endswith('i') or mnemonic in ['lw', 'ld', 'jalr', 'fld']: # I-type loads, ALU imm, jalr, fp loads
                  imm = imm_i(inst_word) #
             elif mnemonic in ['sw', 'sd', 'fsd']: # S-type stores
                  imm = imm_s(inst_word) #
             elif mnemonic.startswith('b'): # B-type branches
                  imm = imm_b(inst_word) #
             elif mnemonic in ['lui', 'auipc']: # U-type
                  imm = imm_u(inst_word) #
             elif mnemonic == 'jal': # J-type
                  imm = imm_j(inst_word) #

    rs1_val, rs2_val = register_file.read(rs1, rs2) #

    return {'pc': pc, 'inst_word': inst_word, 'ctrl': ctrl, 'rs1_val': rs1_val, 'rs2_val': rs2_val, 'imm': imm, 'rd': rd, 'rs1': rs1, 'rs2': rs2, 'mnemonic': mnemonic}


def execute(id_ex_data, forward_a, forward_b, ex_mem_fwd, mem_wb_fwd):
    """Execute instruction: ALU operation, branch target calculation."""
    ctrl = id_ex_data['ctrl']
    pc = id_ex_data['pc']
    inst_word = id_ex_data['inst_word']
    rd = id_ex_data['rd']
    imm = id_ex_data['imm']
    rs1_val_orig = id_ex_data['rs1_val']
    rs2_val_orig = id_ex_data['rs2_val']
    mnemonic = id_ex_data['mnemonic']

    if mnemonic == 'nop':
         return {'pc': pc, 'inst_word': inst_word, 'ctrl': ctrl, 'alu_result': 0, 'rs2_val': 0, 'rd': 0, 'branch_target': 0, 'branch_taken': False, 'mnemonic': 'nop'}

    # --- Apply Forwarding ---
    op1 = rs1_val_orig
    op2_reg = rs2_val_orig

    if forward_a == 1: # Forward from EX/MEM ALU result
        op1 = ex_mem_fwd['alu_result']
        print(f"EX: Forwarded A from EX/MEM result: {op1:#x}")
    elif forward_a == 2: # Forward from MEM/WB result
        op1 = mem_wb_fwd['result'] # 'result' holds writeback data from WB stage
        print(f"EX: Forwarded A from MEM/WB result: {op1:#x}")

    if forward_b == 1: # Forward from EX/MEM ALU result
        op2_reg = ex_mem_fwd['alu_result']
        print(f"EX: Forwarded B from EX/MEM result: {op2_reg:#x}")
    elif forward_b == 2: # Forward from MEM/WB result
        op2_reg = mem_wb_fwd['result'] # 'result' holds writeback data from WB stage
        print(f"EX: Forwarded B from MEM/WB result: {op2_reg:#x}")

    alu_op2 = imm if ctrl['aluSrc'] else op2_reg #

    alu_result = alu(op1, alu_op2, ctrl['aluOp']) #

    # Branch logic
    branch_taken = False
    branch_target = 0
    if ctrl['branch']: #
        alu_op = ctrl['aluOp'] #
        # Use forwarded operands for comparison
        op1_comp = op1
        op2_comp = op2_reg

        # RISC-V branch comparisons
        zero = (op1_comp == op2_comp)
        less_than = (op1_comp < op2_comp) # Signed comparison
        # Need proper 64-bit unsigned comparison
        mask64 = (1 << 64) - 1
        less_than_u = ((op1_comp & mask64) < (op2_comp & mask64)) # Unsigned comparison

        if alu_op == 'beq' and zero: branch_taken = True
        elif alu_op == 'bne' and not zero: branch_taken = True
        elif alu_op == 'blt' and less_than: branch_taken = True
        elif alu_op == 'bge' and not less_than: branch_taken = True
        elif alu_op == 'bltu' and less_than_u: branch_taken = True
        elif alu_op == 'bgeu' and not less_than_u: branch_taken = True

        if branch_taken:
            branch_target = pc + imm
            print(f"EX: Branch {mnemonic} Taken. Target: {branch_target:#x}")
        else:
             print(f"EX: Branch {mnemonic} Not Taken.")

    # Handle Jumps
    is_jump = False
    if mnemonic == 'jal': #
        branch_taken = True # Treat JAL as taken branch for PC update
        branch_target = pc + imm
        alu_result = pc + 4 # JAL saves PC+4 to rd
        ctrl['regWrite'] = 1 # Ensure writeback
        print(f"EX: JAL jump. Target: {branch_target:#x}, Save Addr: {alu_result:#x}")
        is_jump = True
    elif mnemonic == 'jalr': #
        branch_taken = True
        branch_target = (op1 + imm) & ~1 # Target = (rs1+imm) & ~1
        alu_result = pc + 4 # JALR saves PC+4 to rd
        ctrl['regWrite'] = 1 # Ensure writeback
        print(f"EX: JALR jump via x{id_ex_data['rs1']}. Target: {branch_target:#x}, Save Addr: {alu_result:#x}")
        is_jump = True

    return {'pc': pc, 'inst_word': inst_word, 'ctrl': ctrl, 'alu_result': alu_result, 'rs2_val': op2_reg, 'rd': rd, 'branch_target': branch_target, 'branch_taken': branch_taken or is_jump, 'mnemonic': mnemonic}


def memory_access(ex_mem_data, data_memory):
    """Memory access stage: Load or Store data."""
    ctrl = ex_mem_data['ctrl']
    alu_result = ex_mem_data['alu_result'] # Address for load/store
    rs2_val = ex_mem_data['rs2_val'] # Data to store
    rd = ex_mem_data['rd']
    pc = ex_mem_data['pc']
    inst_word = ex_mem_data['inst_word']
    mnemonic = ex_mem_data['mnemonic']

    if mnemonic == 'nop':
         return {'pc': pc, 'inst_word': inst_word, 'ctrl': ctrl, 'mem_data': 0, 'alu_result': 0, 'rd': 0, 'mnemonic': 'nop'}

    mem_data = 0

    if ctrl['memRead']: #
        # Assuming LD for 64-bit (or LW based on your control unit)
        address = alu_result
        if address in data_memory:
            mem_data = data_memory[address]
            print(f"MEM: Load {mnemonic} from Addr {address:#x}. Data: {mem_data:#x}")
        else:
            mem_data = 0
            print(f"MEM: Warning - Load {mnemonic} from uninitialized Addr {address:#x}. Data: 0x0")

    elif ctrl['memWrite']: #
        # Assuming SD for 64-bit (or SW based on control unit)
        address = alu_result
        data_memory[address] = rs2_val
        print(f"MEM: Store {mnemonic} to Addr {address:#x}. Data: {rs2_val:#x}")

    # Pass necessary data to WB stage
    return {'pc': pc, 'inst_word': inst_word, 'ctrl': ctrl, 'mem_data': mem_data, 'alu_result': alu_result, 'rd': rd, 'mnemonic': mnemonic}

def write_back(mem_wb_data, reg_file):
    """Write back result to register file."""
    ctrl = mem_wb_data['ctrl']
    rd = mem_wb_data['rd']
    mem_data = mem_wb_data['mem_data']
    alu_result = mem_wb_data['alu_result']
    mnemonic = mem_wb_data['mnemonic']

    if mnemonic == 'nop':
        return # NOP does nothing

    result = 0
    if ctrl['regWrite']: #
        if rd == 0:
             print(f"WB: Attempted write to x0 ignored for {mnemonic}.")
             return {'result': 0} # Return something for WB fwd consistency

        result = mem_data if ctrl['memToReg'] else alu_result #

        # Assuming integer registers based on RV64IMD focus
        # If D extension is active, check ctrl['fpu'] etc. for fpr write
        reg_file.write(rd, result) #
        print(f"WB: Write x{rd} <- {result:#x} (from {mnemonic})")
    else:
        pass

    # Return the final result written for potential forwarding
    return {'result': result}


# --- Simulation ---

def load_program(program_hex):
    """Loads hex instructions into memory."""
    global memory
    address = 0
    for inst_hex in program_hex:
        try:
            inst_word = int(inst_hex, 16)
            memory[address] = inst_word
            address += 4
        except ValueError:
            print(f"Error: Invalid hex instruction format: {inst_hex}")
            sys.exit(1)
    print(f"Program loaded. {len(program_hex)} instructions.")
    return address

def run_simulation(max_cycles):
    global pc, if_id_reg, id_ex_reg, ex_mem_reg, mem_wb_reg

    cycle = 0
    instructions_retired = 0

    ex_mem_fwd_data = {'alu_result': 0}
    mem_wb_fwd_data = {'result': 0}

    while cycle < max_cycles:
        print(f"\n--- Cycle {cycle} --- PC: {pc:#x} ---")

        # --- 1. Write Back Stage ---
        wb_result_dict = write_back(mem_wb_reg, register_file)
        if mem_wb_reg['inst_word'] != NOP_INSTRUCTION and mem_wb_reg['mnemonic'] != 'nop':
             instructions_retired += 1

        # --- 2. Memory Access Stage ---
        mem_result = memory_access(ex_mem_reg, memory)

        # --- 3. Execute Stage ---
        # Capture data potentially forwarded from later stages (state BEFORE update this cycle)
        ex_mem_fwd_data = {'alu_result': ex_mem_reg.get('alu_result', 0), 'rd': ex_mem_reg.get('rd',0), 'ctrl': ex_mem_reg.get('ctrl', {})}
        mem_wb_fwd_data = {'result': wb_result_dict.get('result', 0) if wb_result_dict else 0, 'rd': mem_wb_reg.get('rd',0), 'ctrl': mem_wb_reg.get('ctrl', {})}

        ex_result = execute(id_ex_reg,
                             hazard_unit.forward_a_ex, hazard_unit.forward_b_ex,
                             ex_mem_fwd_data, mem_wb_fwd_data)

        # --- 4. Decode Stage ---
        if not hazard_unit.stall_id:
            if hazard_unit.flush_id_ex:
                print("ID: Flushing ID/EX register")
                id_result = {'pc': 0, 'inst_word': NOP_INSTRUCTION, 'ctrl': get_control_signals('nop'), 'rs1_val': 0, 'rs2_val': 0, 'imm': 0, 'rd': 0, 'rs1': 0, 'rs2': 0, 'mnemonic': 'nop'} #
            else:
                id_result = decode(if_id_reg)
        else:
             print("ID: Stalled.")
             id_result = id_ex_reg # Keep previous state

        # --- 5. Fetch Stage ---
        next_pc = pc # Default next PC
        pc_updated_by_branch = False
        if not hazard_unit.stall_if:
            if hazard_unit.flush_if_id:
                 print("IF: Flushing IF/ID register")
                 if_result = {'pc': 0, 'inst_word': NOP_INSTRUCTION} # Flush with NOP
            elif ex_result and ex_result.get('branch_taken'):
                 # PC update handled later based on EX result this cycle
                 next_pc = ex_result['branch_target']
                 pc_updated_by_branch = True
                 print(f"IF: PC will update to {next_pc:#x} due to EX branch/jump")
                 if_result = fetch(pc) # Fetch current PC before update; will be flushed
                 # Schedule flush for the instruction *currently* in IF/ID
                 hazard_unit.flush_if_id = True
            else:
                 if_result = fetch(pc)
                 next_pc = pc + 4 # Default PC increment
        else:
            print("IF: Stalled.")
            if_result = None # No new fetch result

        # --- Hazard Detection (Based on state *before* register update) ---
        hazard_unit.detect_and_resolve(id_ex_reg, ex_mem_reg, mem_wb_reg)

        # --- Update PC ---
        if not hazard_unit.stall_if: # Only update PC if IF is not stalled
             pc = next_pc

        # --- Update Pipeline Registers ---
        # Update happens *after* stages compute results and hazards are detected
        mem_wb_reg = mem_result

        if hazard_unit.stall_ex: # Handle load-use stall
             # EX/MEM keeps its value, effectively inserting a bubble delay
             print("EX/MEM: Holding due to EX stall.")
             # No change to ex_mem_reg
        elif hazard_unit.flush_id_ex: # Handle flush due to branch/load-use stall
             ex_mem_reg = {'pc': 0, 'inst_word': NOP_INSTRUCTION, 'ctrl': get_control_signals('nop'), 'alu_result': 0, 'rs2_val': 0, 'rd': 0, 'branch_target': 0, 'branch_taken': False, 'mnemonic': 'nop'} #
             print("EX/MEM: Receiving flushed NOP.")
        else:
             ex_mem_reg = ex_result
             # print(f"EX/MEM: Updated with {ex_result.get('mnemonic')}")


        if hazard_unit.stall_id:
            print("ID/EX: Holding due to ID stall.")
            # No change to id_ex_reg
        elif hazard_unit.flush_id_ex: # Check again (can be set by branch this cycle)
             id_ex_reg = {'pc': 0, 'inst_word': NOP_INSTRUCTION, 'ctrl': get_control_signals('nop'), 'rs1_val': 0, 'rs2_val': 0, 'imm': 0, 'rd': 0, 'rs1': 0, 'rs2': 0, 'mnemonic': 'nop'} #
             print("ID/EX: Receiving flushed NOP.")
        else:
            id_ex_reg = id_result
            # print(f"ID/EX: Updated with {id_result.get('mnemonic')}")


        if hazard_unit.stall_if:
            print("IF/ID: Holding due to IF stall.")
             # No change to if_id_reg
        elif hazard_unit.flush_if_id:
            if_id_reg = {'pc': 0, 'inst_word': NOP_INSTRUCTION}
            print("IF/ID: Receiving flushed NOP.")
        elif if_result:
            if_id_reg = if_result
            # print(f"IF/ID: Updated with {if_result.get('inst_word'):#010x}")


        # Print pipeline register contents for debugging
        print(f"Regs: IF/ID: {if_id_reg.get('inst_word',0):#010x} ID/EX: {id_ex_reg.get('mnemonic','-')}({id_ex_reg.get('inst_word',0):#010x}) EX/MEM: {ex_mem_reg.get('mnemonic','-')}({ex_mem_reg.get('inst_word',0):#010x}) MEM/WB: {mem_wb_reg.get('mnemonic','-')}({mem_wb_reg.get('inst_word',0):#010x})")


        cycle += 1

        if cycle > max_cycles - 1 :
             print("\nMax cycles reached.")
             break
        # More robust termination: Check if pipeline is empty and no more instructions are fetched
        if pc >= MEM_SIZE and if_id_reg['inst_word'] == NOP_INSTRUCTION and id_ex_reg['inst_word'] == NOP_INSTRUCTION and ex_mem_reg['inst_word'] == NOP_INSTRUCTION and mem_wb_reg['inst_word'] == NOP_INSTRUCTION:
              print("\nPipeline empty. Halting.")
              # Add a few extra cycles for last instruction to finish WB
              if mem_wb_reg.get('inst_word', NOP_INSTRUCTION) != NOP_INSTRUCTION or \
                 ex_mem_reg.get('inst_word', NOP_INSTRUCTION) != NOP_INSTRUCTION or \
                 id_ex_reg.get('inst_word', NOP_INSTRUCTION) != NOP_INSTRUCTION:
                  print("Waiting for pipeline drain...")
                  continue # Allow final instructions to finish
              else:
                  break


    print(f"\n--- Simulation Finished ---")
    print(f"Cycles: {cycle}")
    print(f"Instructions Retired: {instructions_retired}")
    print(f"Final PC: {pc:#x}")
    register_file.dump() #
    print("\nMemory State (non-zero):")
    for addr, value in sorted(memory.items()):
        # Only print data memory changes, assuming program code doesn't change
        # This requires knowing the program size or memory layout.
        # Simple approach: print non-zero values at addresses < some threshold
         if value != 0 and addr < 0x200: # Example threshold
              print(f"  {addr:#06x}: {value:#018x}")



# --- Main Execution ---
if __name__ == "__main__":
    # Example Program from previous response
    program = [
        "0x00500093", # 00: addi x1, x0, 5
        "0x00A00113", # 04: addi x2, x0, 10
        "0x002081B3", # 08: add x3, x1, x2  (Data Hazard x1, x2 -> Forwarding)
        "0x00302023", # 0C: sd x3, 0(x0)   (Data Hazard x3 -> Forwarding)
        "0x00003203", # 10: ld x4, 0(x0)
        "0x00120293", # 14: addi x5, x4, 1  (Load-Use Hazard x4 -> Stall + Forward)
        "0x00129863", # 18: bne x5, x1, +8 (target=0x20) (Control Hazard -> Flush if taken)
        "0x00100313", # 1C: addi x6, x0, 1 (skipped if branch taken)
        "0x00200393", # 20: addi x7, x0, 2 (target label)
        "0x00000013"  # 24: NOP
    ]

    program_end_addr = load_program(program)

    run_simulation(max_cycles=50)