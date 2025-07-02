// main.cpp: Full RISC-V 5-stage pipeline simulator in C++ (Enhanced Output)

#include <bits/stdc++.h>
using namespace std;

// --- Constants ---
static const size_t MEM_SIZE = 1024 * 10; // 10 KB data memory (sparse)
static const double FLOAT_ZERO = 0.0;

// --- Instruction / Pipeline Register ---
struct Instruction {
    string   op;
    int      rd, rs1, rs2;
    int64_t  imm;
    bool     is_fp;
    string   raw_str;
    int      pc;

    int64_t rs1_val, rs2_val;
    double  fs1_val, fs2_val;
    int64_t alu_result;
    double  fpu_result;

    int64_t rs2_val_mem;
    double  fs2_val_mem;
    bool    mem_read, mem_write;
    bool    fp_mem_read, fp_mem_write;

    bool    reg_write, fp_reg_write;
    int     write_reg, write_fp_reg;

    bool    branch_taken;
    int     jump_target;

    int64_t mem_data;
    int64_t alu_result_wb;
    double  fp_mem_data;
    double  fpu_result_wb;
    bool    mem_read_wb, fp_mem_read_wb;

    Instruction()
        : op("NOP"), rd(0), rs1(0), rs2(0), imm(0), is_fp(false), raw_str("NOP"), pc(-1),
          rs1_val(0), rs2_val(0), fs1_val(0.0), fs2_val(0.0), alu_result(0), fpu_result(0.0),
          rs2_val_mem(0), fs2_val_mem(0.0), mem_read(false), mem_write(false),
          fp_mem_read(false), fp_mem_write(false), reg_write(false), fp_reg_write(false),
          write_reg(-1), write_fp_reg(-1), branch_taken(false), jump_target(-1),
          mem_data(0), alu_result_wb(0), fp_mem_data(0.0), fpu_result_wb(0.0),
          mem_read_wb(false), fp_mem_read_wb(false) {}
};

// --- Utility Functions ---
int64_t double_to_int64(double f) {
    int64_t bits;
    memcpy(&bits, &f, sizeof(f));
    return bits;
}

double int64_to_double(int64_t bits) {
    double f;
    memcpy(&f, &bits, sizeof(f));
    return f;
}

string trim(const string& s) {
    auto l = s.find_first_not_of(" \t\r\n");
    auto r = s.find_last_not_of(" \t\r\n");
    return (l == string::npos) ? "" : s.substr(l, r - l + 1);
}

string up(const string& s) {
    string out = s;
    transform(out.begin(), out.end(), out.begin(), ::toupper);
    return out;
}

vector<string> tokenize(string s) {
    for (char& c : s) if (c == ',' || c == '(' || c == ')') c = ' ';
    istringstream iss(s);
    vector<string> parts;
    string t;
    while (iss >> t) parts.push_back(t);
    return parts;
}

// --- Processor ---
class Processor {
    const vector<string> I_ALU_OPS = {"ADDI","SLTI","SLTIU","XORI","ORI","ANDI","SLLI","SRLI","SRAI"};
    const vector<string> LOAD_OPS   = {"LW","FLD","JALR"};
    const vector<string> STORE_OPS  = {"SW","FSD"};
    const vector<string> BRANCH_OPS = {"BEQ","BNE","BLT","BGE","BLTU","BGEU"};
    const vector<string> R_TYPE_OPS = {"ADD","SUB","SLL","SLT","SLTU","XOR","SRL","SRA","OR","AND","FADD.D","FSUB.D","FMUL.D","FDIV.D"};

public:
    int pc = 0, clock = 0;
    vector<int64_t> regs = vector<int64_t>(32, 0);
    vector<double>  fpregs = vector<double>(32, 0.0);
    unordered_map<int64_t,int64_t> data_mem;
    map<int,Instruction> instr_mem;
    unordered_map<string,int> labels;
    Instruction IF_ID, ID_EX, EX_MEM, MEM_WB;
    bool stall = false, flush = false;
    int branch_target_pc = -1;
    int instructions_executed = 0;

    Processor(const vector<string>& ins_in) {
        // same init logic...
        int addr = 0;
        for (const auto& ln : ins_in) {
            string s = trim(ln);
            if (s.empty() || s[0]=='#') continue;
            if (s.back()==':') labels[s.substr(0,s.size()-1)] = addr;
            else addr += 4;
        }
        addr = 0; int ln=0;
        for (const auto& raw: ins_in) {
            ln++;
            string s = trim(raw);
            if (s.empty()||s[0]=='#'||s.back()==':') continue;
            Instruction instr = parse_instruction(raw, addr, ln);
            if (instr.op != "Unsupported") {
                instr.pc = addr;
                instr.raw_str = trim(raw);
                instr_mem[addr] = instr;
                addr += 4;
            }
        }
        IF_ID = ID_EX = EX_MEM = MEM_WB = Instruction();
    }

    void run(int maxc=100) {
        // Initial header
        cout << "=== RISC-V Pipeline Simulator ===\n";
        cout << "Loaded " << instr_mem.size() << " instructions. Starting simulation...\n\n";

        data_mem[64] = double_to_int64(3.14);
        bool empty = false;
        while (clock < maxc && !empty) {
            run_cycle();
            bool allnop = (IF_ID.pc==-1 && ID_EX.pc==-1 && EX_MEM.pc==-1 && MEM_WB.pc==-1);
            if (allnop && !instr_mem.count(pc)) empty = true;
        }

        // Final summary
        cout << "--- Simulation Complete ---\n";
        cout << "Cycles: " << clock << ", Instructions: " << instructions_executed
             << ", CPI: " << fixed << setprecision(2)
             << double(clock)/max(1, instructions_executed) << "\n\n";

        // Final register dump (non-zero only)
        cout << "Integer Registers:\n";
        for (int i = 0; i < 32; ++i) {
            if (regs[i] != 0)
                cout << "x" << setw(2) << i << "=" << regs[i] << "  ";
        }
        cout << "\n\nFloating-Point Registers:\n";
        for (int i = 0; i < 32; ++i) {
            if (fpregs[i] != 0.0)
                cout << "f" << setw(2) << i << "=" << fixed << setprecision(2) << fpregs[i] << "  ";
        }
        cout << "\n";

        // Full register dump
        cout << "\n\nFull Register Dump:\n";
        cout << "Integer Registers:\n";
        for (int i = 0; i < 32; ++i) {
            cout << "x" << setw(2) << i << " = " << regs[i] << ((i % 4 == 3) ? "\n" : "\t");
        }
        cout << "\nFloating-Point Registers:\n";
        for (int i = 0; i < 32; ++i) {
            cout << "f" << setw(2) << i << " = " << fixed << setprecision(4) << fpregs[i] << ((i % 4 == 3) ? "\n" : "\t");
        }

    }

private:
    Instruction parse_instruction(const string& raw, int addr, int ln) {
        auto parts = tokenize(raw);
        Instruction instr;
        if (parts.empty()) return instr;

        instr.op    = up(parts[0]);
        instr.is_fp = (instr.op.rfind('F',0)==0);

        try {
            // I-Type ALU
            if (find(I_ALU_OPS.begin(), I_ALU_OPS.end(), instr.op) != I_ALU_OPS.end()) {
                instr.rd   = stoi(parts[1].substr(1));
                instr.rs1  = stoi(parts[2].substr(1));
                instr.imm  = stoll(parts[3], nullptr, 0);
                instr.is_fp= (parts[1][0]=='f');
            }
            // Load / JALR
            else if (find(LOAD_OPS.begin(), LOAD_OPS.end(), instr.op) != LOAD_OPS.end()) {
                instr.rd   = stoi(parts[1].substr(1));
                instr.imm  = stoll(parts[2], nullptr, 0);
                instr.rs1  = stoi(parts[3].substr(1));
                instr.is_fp= (parts[1][0]=='f');
            }
            // Store
            else if (find(STORE_OPS.begin(), STORE_OPS.end(), instr.op) != STORE_OPS.end()) {
                instr.rs2  = stoi(parts[1].substr(1));
                instr.imm  = stoll(parts[2], nullptr, 0);
                instr.rs1  = stoi(parts[3].substr(1));
                instr.is_fp= (parts[1][0]=='f');
            }
            // Branch
            else if (find(BRANCH_OPS.begin(), BRANCH_OPS.end(), instr.op) != BRANCH_OPS.end()) {
                instr.rs1 = stoi(parts[1].substr(1));
                instr.rs2 = stoi(parts[2].substr(1));
            }
            // R-Type (int and FP)
            else if (find(R_TYPE_OPS.begin(), R_TYPE_OPS.end(), instr.op) != R_TYPE_OPS.end()) {
                instr.rd   = stoi(parts[1].substr(1));
                instr.rs1  = stoi(parts[2].substr(1));
                instr.rs2  = stoi(parts[3].substr(1));
                instr.is_fp= (parts[1][0]=='f');
            }
            // JAL
            else if (instr.op=="JAL") {
                instr.rd = stoi(parts[1].substr(1));
            }
            // NOP is fine, anything else unsupported
            else if (instr.op!="NOP") {
                cerr << "Warning: Unsupported instr ln "<<ln<<": "<<raw<<"\n";
                instr.op = "Unsupported";
            }
        } catch(...) {
            cerr << "Parse error ln "<<ln<<": "<<raw<<"\n";
            instr.op = "Unsupported";
        }

        return instr;
    }

    void run_cycle() {
        clock++;

        wb_stage();
        mem_stage();
        ex_stage();
        id_stage();
        if_stage();

        print_pipeline_state();

        if      (stall)                   stall=false;
        else if (branch_target_pc!=-1) { pc=branch_target_pc; branch_target_pc=-1; flush=false; }
        else                             pc+=4;
    }

    void wb_stage() {
        if (MEM_WB.pc==-1) return;

        if (MEM_WB.reg_write && MEM_WB.write_reg>0) {
            regs[MEM_WB.write_reg] = MEM_WB.mem_read_wb ? MEM_WB.mem_data : MEM_WB.alu_result_wb;
        }
        else if (MEM_WB.fp_reg_write && MEM_WB.write_fp_reg>=0) {
            fpregs[MEM_WB.write_fp_reg] = MEM_WB.fp_mem_read_wb ? MEM_WB.fp_mem_data : MEM_WB.fpu_result_wb;
        }

        if (MEM_WB.op!="NOP")
            instructions_executed++;
    }

    void mem_stage() {
        MEM_WB = EX_MEM;
        if (MEM_WB.pc==-1) return;

        int64_t addr = MEM_WB.alu_result;
        if (MEM_WB.mem_write)  data_mem[addr] = MEM_WB.rs2_val_mem;
        if (MEM_WB.fp_mem_write) data_mem[addr] = double_to_int64(MEM_WB.fs2_val_mem);

        if (MEM_WB.mem_read)    MEM_WB.mem_data    = data_mem[addr];
        if (MEM_WB.fp_mem_read) MEM_WB.fp_mem_data = int64_to_double(data_mem[addr]);

        MEM_WB.alu_result_wb   = MEM_WB.alu_result;
        MEM_WB.fpu_result_wb   = MEM_WB.fpu_result;
        MEM_WB.mem_read_wb     = MEM_WB.mem_read;
        MEM_WB.fp_mem_read_wb  = MEM_WB.fp_mem_read;
    }

    void ex_stage() {
        // 1) latch from ID/EX
        EX_MEM = ID_EX;
        if (EX_MEM.pc == -1) return;
    
        // 2) (optional) forwarding hooks would go here…
    
        // 3) carry-through of rs2/fs2 for stores
        EX_MEM.rs2_val_mem = EX_MEM.rs2_val;
        EX_MEM.fs2_val_mem = EX_MEM.fs2_val;
    
        // handy locals
        int64_t op1 = EX_MEM.rs1_val;
        int64_t op2 = EX_MEM.rs2_val;
        double  fp1 = EX_MEM.fs1_val;
        double  fp2 = EX_MEM.fs2_val;
        const string& op = EX_MEM.op;
    
        // 4) ALU / address calculation
        if (EX_MEM.mem_read || EX_MEM.mem_write) {
            // load/store address = base + imm
            EX_MEM.alu_result = op1 + EX_MEM.imm;
        }
        else if (find(I_ALU_OPS.begin(), I_ALU_OPS.end(), op) != I_ALU_OPS.end()) {
            // I‑type integer
            if      (op=="ADDI")  EX_MEM.alu_result = op1 + EX_MEM.imm;
            else if (op=="SLTI")  EX_MEM.alu_result = (op1 < EX_MEM.imm);
            else if (op=="SLTIU") EX_MEM.alu_result = (uint64_t(op1) < uint64_t(EX_MEM.imm));
            else if (op=="XORI")  EX_MEM.alu_result = op1 ^ EX_MEM.imm;
            else if (op=="ORI")   EX_MEM.alu_result = op1 | EX_MEM.imm;
            else if (op=="ANDI")  EX_MEM.alu_result = op1 & EX_MEM.imm;
            else if (op=="SLLI")  EX_MEM.alu_result = op1 << EX_MEM.imm;
            else if (op=="SRLI")  EX_MEM.alu_result = uint64_t(op1) >> EX_MEM.imm;
            else if (op=="SRAI")  EX_MEM.alu_result = op1 >> EX_MEM.imm;
        }
        else if (find(R_TYPE_OPS.begin(), R_TYPE_OPS.end(), op) != R_TYPE_OPS.end()) {
            // R‑type integer
            if      (op=="ADD")   EX_MEM.alu_result = op1 + op2;
            else if (op=="SUB")   EX_MEM.alu_result = op1 - op2;
            else if (op=="SLL")   EX_MEM.alu_result = op1 << (op2 & 0x3F);
            else if (op=="SLT")   EX_MEM.alu_result = (op1 < op2);
            else if (op=="SLTU")  EX_MEM.alu_result = (uint64_t(op1) < uint64_t(op2));
            else if (op=="XOR")   EX_MEM.alu_result = op1 ^ op2;
            else if (op=="SRL")   EX_MEM.alu_result = uint64_t(op1) >> (op2 & 0x3F);
            else if (op=="SRA")   EX_MEM.alu_result = op1 >> (op2 & 0x3F);
            else if (op=="OR")    EX_MEM.alu_result = op1 | op2;
            else if (op=="AND")   EX_MEM.alu_result = op1 & op2;
            // R‑type FP
            else if (op=="FADD.D") EX_MEM.fpu_result = fp1 + fp2;
            else if (op=="FSUB.D") EX_MEM.fpu_result = fp1 - fp2;
            else if (op=="FMUL.D") EX_MEM.fpu_result = fp1 * fp2;
            else if (op=="FDIV.D") EX_MEM.fpu_result = fp1 / fp2;
        }
    
        // 5) Branch instructions
        if (find(BRANCH_OPS.begin(), BRANCH_OPS.end(), op) != BRANCH_OPS.end()) {
            bool cond = false;
            if      (op=="BEQ")  cond = (op1 == op2);
            else if (op=="BNE")  cond = (op1 != op2);
            else if (op=="BLT")  cond = (op1 <  op2);
            else if (op=="BGE")  cond = (op1 >= op2);
            else if (op=="BLTU") cond = (uint64_t(op1) < uint64_t(op2));
            else if (op=="BGEU") cond = (uint64_t(op1) >= uint64_t(op2));
            if (cond) {
                string lbl = trim(EX_MEM.raw_str.substr(EX_MEM.raw_str.find_last_of(' ')+1));
                EX_MEM.branch_taken = true;
                branch_target_pc     = labels[lbl];
                flush                = true;
            }
        }
    
        // 6) JAL
        if (op=="JAL") {
            EX_MEM.alu_result = EX_MEM.pc + 4;
            EX_MEM.reg_write  = true;
            EX_MEM.write_reg  = EX_MEM.rd;
            string lbl = trim(EX_MEM.raw_str.substr(EX_MEM.raw_str.find_last_of(' ')+1));
            branch_target_pc = labels[lbl];
            flush            = true;
        }
    
        // 7) JALR
        if (op=="JALR") {
            EX_MEM.alu_result = EX_MEM.pc + 4;
            EX_MEM.reg_write  = true;
            EX_MEM.write_reg  = EX_MEM.rd;
            branch_target_pc = (EX_MEM.rs1_val + EX_MEM.imm) & ~1;
            flush            = true;
        }
    }
    

    void id_stage() {
        if (stall) {
            ID_EX = Instruction();
            return;
        }
        if (flush) {
            ID_EX = Instruction();
            return;
        }
    
        // 1) latch the fetched instruction
        ID_EX = IF_ID;
        if (ID_EX.pc == -1) return;
    
        // 2) read register operands
        ID_EX.rs1_val = regs[ID_EX.rs1];
        ID_EX.rs2_val = regs[ID_EX.rs2];
        ID_EX.fs1_val = fpregs[ID_EX.rs1];
        ID_EX.fs2_val = fpregs[ID_EX.rs2];
    
        // 3) set up control signals
        ID_EX.mem_read     = find(LOAD_OPS.begin(), LOAD_OPS.end(), ID_EX.op) != LOAD_OPS.end();
        ID_EX.mem_write    = find(STORE_OPS.begin(), STORE_OPS.end(), ID_EX.op) != STORE_OPS.end();
        ID_EX.fp_mem_read  = (ID_EX.op == "FLD");
        ID_EX.fp_mem_write = (ID_EX.op == "FSD");
    
        bool isI = find(I_ALU_OPS.begin(), I_ALU_OPS.end(), ID_EX.op) != I_ALU_OPS.end();
        bool isR = find(R_TYPE_OPS.begin(), R_TYPE_OPS.end(), ID_EX.op) != R_TYPE_OPS.end();
        ID_EX.reg_write    = (!ID_EX.is_fp && (isI || isR || ID_EX.op=="LW" || ID_EX.op=="JAL" || ID_EX.op=="JALR"));
        ID_EX.fp_reg_write = ( ID_EX.is_fp && (isR || ID_EX.op=="FLD") );
        ID_EX.write_reg    = ID_EX.rd;
        ID_EX.write_fp_reg = ID_EX.rd;
    
        // 4) load‐use hazard detection (unchanged)
        bool haz = false;
        if (EX_MEM.mem_read && EX_MEM.write_reg>0 &&
            (ID_EX.rs1==EX_MEM.write_reg || ID_EX.rs2==EX_MEM.write_reg)) {
            haz = true;
        }
        if (EX_MEM.fp_mem_read && EX_MEM.write_fp_reg>=0 &&
            (ID_EX.rs1==EX_MEM.write_fp_reg || ID_EX.rs2==EX_MEM.write_fp_reg)) {
            haz = true;
        }
        if (haz) {
            stall = true;
            ID_EX  = Instruction();
        }
    }
    

    void if_stage() {
        if (stall) return;
        if (flush) {
            IF_ID = Instruction();
            return;
        }

        if (instr_mem.count(pc))
            IF_ID = instr_mem[pc];
        else
            IF_ID = Instruction();
    }


    void print_pipeline_state() {
        static vector<int64_t> prev_regs(32, 0);
        static vector<double> prev_fpregs(32, 0.0);

        cout << "[Cycle " << setw(2) << clock << "] "
             << "PC=0x" << hex << pc << dec;
        if (stall) cout << " (Stall)";
        if (flush) cout << " (Flush)";
        cout << "\n";

        // Helper to dump a stage's raw instruction and its detailed register outputs
        auto dump_stage = [&](const string& stage, const Instruction& r) {
            if (r.pc == -1) {
                cout << "  " << setw(7) << stage << ": NOP\n";
                return;
            }
            cout << "  " << setw(7) << stage << ": " << r.raw_str;
            if (r.reg_write)   cout << "  -> x" << r.write_reg;
            if (r.fp_reg_write)cout << "  -> f" << r.write_fp_reg;
            cout << "\n";
            // Now print the stage-specific register values
            cout << "    [" << stage << " regs] pc=" << r.pc;
            if (stage == "IF/ID") {
                // nothing additional
            } else if (stage == "ID/EX") {
                cout << " rs1=x" << r.rs1 << "(" << r.rs1_val << ")";
                cout << " rs2=x" << r.rs2 << "(" << r.rs2_val << ")";
                cout << " imm=" << r.imm;
            } else if (stage == "EX/MEM") {
                cout << " alu_res=" << r.alu_result;
                cout << " mem_rd=" << r.mem_read << " mem_wr=" << r.mem_write;
                cout << " rs2_mem_val=" << r.rs2_val_mem;
            } else if (stage == "MEM/WB") {
                cout << " mem_data=" << r.mem_data;
                cout << " alu_res_wb=" << r.alu_result_wb;
                cout << " mem_rd_wb=" << r.mem_read_wb;
            }
            cout << "\n";
        };

        dump_stage("IF/ID", IF_ID);
        dump_stage("ID/EX", ID_EX);
        dump_stage("EX/MEM", EX_MEM);
        dump_stage("MEM/WB", MEM_WB);

        // Show registers that changed
        cout << "  Register Changes: ";
        bool changed = false;
        for (int i = 0; i < 32; ++i) {
            if (regs[i] != prev_regs[i]) {
                cout << "x" << i << "=" << regs[i] << " ";
                changed = true;
            }
        }
        for (int i = 0; i < 32; ++i) {
            if (abs(fpregs[i] - prev_fpregs[i]) > 1e-9) {
                cout << "f" << i << "=" << fixed << setprecision(2) << fpregs[i] << " ";
                changed = true;
            }
        }
        if (!changed) cout << "(none)";
        cout << "\n------------------------------\n";

        // Save snapshot
        prev_regs = regs;
        prev_fpregs = fpregs;
    }
};

int main() {
    vector<string> instructions = {
        // Immediate arithmetic
        "ADDI x1, x0, 20",     // x1 = 20
        "ADDI x2, x0, -5",     // x2 = -5 (sign-extend)
        "SLTI x3, x1, 10",     // x3 = (20 < 10)?0:0
        "XORI x4, x2, 0xFF",   // x4 = x2 ^ 0xFF
        "ORI x5, x2, 0xF0",    // x5 = x2 | 0xF0
        "ANDI x6, x1, 0x1F",   // x6 = x1 & 0x1F
        "SLLI x7, x1, 2",      // x7 = x1 << 2
        "SRLI x8, x1, 1",      // x8 = x1 >> 1 (logical)
        "SRAI x9, x2, 1",      // x9 = x2 >> 1 (arithmetic)

        // Register-register arithmetic
        "ADD x10, x1, x2",     // x10 = 20 + (-5)
        "SUB x11, x1, x2",     // x11 = 20 - (-5)
        "SLL x12, x1, x2",     // x12 = x1 << (x2 & 0x3F)
        "SRL x13, x1, x2",     // x13 = x1 >> (x2 & 0x3F)
        "SRA x14, x1, x2",     // x14 = x1 >> signed(x2 & 0x3F)
        "SLT x15, x2, x1",     // x15 = 1
        "SLTU x16, x2, x1",    // x16 = 0 (unsigned)
        "XOR x17, x1, x2",     // x17 = x1 ^ x2
        "OR x18, x1, x2",      // x18 = x1 | x2
        "AND x19, x1, x2",     // x19 = x1 & x2

        // Memory operations
        "SW x10, 0(x1)",       // Mem[20] = x10
        "LW x20, 0(x1)",       // x20 = Mem[20]

        // Branch & labels
        "BEQ x10, x20, equal_label", // taken
        "ADDI x21, x0, 1",     // skipped
        "JAL x0, post_branch",// skip next
        "equal_label:",
        "ADDI x21, x0, 2",     // x21 = 2
        "post_branch:",

        // JAL & JALR
        "JAL x22, jal_target", // x22 = return addr
        "JALR x23, 8(x1)",     // x23 = return addr, PC = 20+8
        "jal_target:",
        "ADDI x24, x0, 3",     // test after JAL

        // Floating-point ops
        "FLD f1, 64(x0)",      // load 3.14 (init)
        "FADD.D f2, f1, f1",   // double
        "FSUB.D f3, f2, f1",   // subtract
        "FMUL.D f4, f2, f2",   // multiply
        "FDIV.D f5, f4, f1",   // divide
        "FSD f5, 128(x0)",     // store result

        // Final write-back test
        "ADDI x30, x0, 999"    // sentinel
    };
    Processor proc(instructions);
    proc.run(45);
    return 0;
}
