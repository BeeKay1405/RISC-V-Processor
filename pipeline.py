#AKSHAT BKL WRITE UR CODE FOR PHASE 5 HERE 



# Memory Stage
def mem_stage(ex_mem, mem_wb, memory):
    mem_wb.clear()
    
    mem_wb["rd"] = ex_mem.get("rd")
    mem_wb["reg_write"] = ex_mem.get("reg_write")
    mem_wb["mem_to_reg"] = ex_mem.get("mem_to_reg")
    mem_wb["alu_result"] = ex_mem.get("alu_result")
    mem_wb["fp_op"] = ex_mem.get("fp_op", False)  # for WB to know if float
    mem_wb["float_write"] = ex_mem.get("float_write", False)

    addr = ex_mem.get("alu_result")
    rs2_val = ex_mem.get("rs2_val")
    opcode = ex_mem.get("opcode")

    if opcode in ["lw", "ld", "flw", "fld"]:
        # Load from memory
        val = memory.get(addr, 0)
        mem_wb["mem_data"] = val

    elif opcode in ["sw", "sd", "fsw", "fsd"]:
        # Store to memory
        memory[addr] = rs2_val
        mem_wb["mem_data"] = None  # nothing to write back

    else:
        mem_wb["mem_data"] = None  # ALU result only


# Write Back Stage
def wb_stage(mem_wb, reg_file, fp_reg_file):
    rd = mem_wb.get("rd")
    reg_write = mem_wb.get("reg_write", False)
    mem_to_reg = mem_wb.get("mem_to_reg", False)
    alu_result = mem_wb.get("alu_result")
    mem_data = mem_wb.get("mem_data")
    fp_op = mem_wb.get("fp_op", False)
    float_write = mem_wb.get("float_write", False)

    if reg_write and rd is not None:
        write_data = mem_data if mem_to_reg else alu_result

        if float_write:
            fp_reg_file.write(rd, write_data)
        else:
            reg_file.write(rd, write_data)
