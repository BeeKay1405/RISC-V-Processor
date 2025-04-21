# hazard_unit.py

class HazardUnit:
    def detect_load_use_hazard(self, id_ex, ex_mem):
        # Only worry if the EX instruction is a load (mem_to_reg)
        if ex_mem.get("mem_to_reg"):
            rd_ex = ex_mem.get("rd")
            rs1_id = id_ex.get("rs1")
            rs2_id = id_ex.get("rs2")

            if rd_ex is not None and rd_ex != 0:
                return rd_ex == rs1_id or rd_ex == rs2_id
        return False
