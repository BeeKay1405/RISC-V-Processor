#utils.py
#This file is for keeping binary number manipulation functions and all the decoding functions

from isa import OPCODES, FUNCT3, FUNCT7

def getBits(value : int, hi : int, lo : int) -> int:
    """
    Return bits from 'hi' to 'lo' in the binary representation of 'value'
    """
    value = value >> lo
    mask = (1 << (hi - lo + 1)) - 1
    value = value & mask
    return value

def signExtend(value : int, bits: int) -> int:
    """
    Sign-extend the binary representation of 'value' to 'bits' number of bits.
    """
    signBit = 1 << (bits - 1)
    value = (value & (signBit - 1)) - (value & signBit)
    return value


def fieldsGen(instWord : int) -> dict:
    """
    Given a 32-bit instruction 'instWord', break it down into the fields
    Some of these fields are useless for some types of instructions.
    """
    fields = {}
    fields['opcode'] = getBits(instWord, 6, 0)
    fields['rd'] = getBits(instWord, 11, 7)
    fields['funct3'] = getBits(instWord, 14, 12)
    fields['rs1'] = getBits(instWord, 19, 15)
    fields['rs2'] = getBits(instWord, 24, 20)
    fields['funct7'] = getBits(instWord, 31, 25)
    return fields

def imm(instWord : int, type : str) -> int:
    """
    Call the correct function depending on the 'type' of instruction.
    """
    if type == 'i': return imm_i(instWord)
    if type == 's': return imm_s(instWord)
    if type == 'b': return imm_b(instWord)
    if type == 'u': return imm_u(instWord)
    else:
        return imm_j(instWord)

def imm_i(instWord: int) -> int:
    """
    I-type immediate: bits [31:20], sign-extended to 64 bits.
    """
    raw = getBits(instWord, 31, 20)
    return signExtend(raw, 12)


def imm_s(instWord: int) -> int:
    """
    S-type immediate: bits [31:25] << 5 | bits [11:7], sign-extended.
    """
    hi = getBits(instWord, 31, 25)
    lo = getBits(instWord, 11, 7)
    raw = (hi << 5) | lo
    return signExtend(raw, 12)


def imm_b(instWord: int) -> int:
    """
    B-type immediate: bits [31] (sign), [7] (bit 11), [30:25] (bits 10:5), [11:8] (bits 4:1), then <<1.
    """
    bit12   = getBits(instWord, 31, 31)
    bit11   = getBits(instWord, 7, 7)
    bits10_5= getBits(instWord, 30, 25)
    bits4_1 = getBits(instWord, 11, 8)
    raw = (bit12 << 12) | (bit11 << 11) | (bits10_5 << 5) | (bits4_1 << 1)
    return signExtend(raw, 13)


def imm_u(instWord: int) -> int:
    """
    U-type immediate: bits [31:12] << 12.
    """
    raw = getBits(instWord, 31, 12) << 12
    return signExtend(raw, 32)  # effectively zero-extended above bit 31


def imm_j(instWord: int) -> int:
    """
    J-type immediate: bits [31] (sign), [19:12], [20], [30:21], then <<1.
    """
    bit20    = getBits(instWord, 31, 31)
    bits19_12= getBits(instWord, 19, 12)
    bit11    = getBits(instWord, 20, 20)
    bits10_1 = getBits(instWord, 30, 21)
    raw = (bit20 << 20) | (bits19_12 << 12) | (bit11 << 11) | (bits10_1 << 1)
    return signExtend(raw, 21)

def decodeInstruction(instWord: int) -> str:
    """
    Decode the instruction word into its assembly mnemonic.
    Looks up OPCODES, then FUNCT3, then FUNCT7 (and for R4,
    checks the upper bits of funct7 as needed).
    """
    fields = fieldsGen(instWord)
    opc = fields['opcode']
    # Find candidates by opcode
    candidates = [name for name,code in OPCODES.items() if code == opc]
    # Further filter by funct3
    f3 = fields['funct3']
    candidates = [name for name in candidates if FUNCT3.get(name) == f3]
    # Filter by funct7 if needed
    if len(candidates) > 1 and any(name in FUNCT7 for name in candidates):
        f7 = fields['funct7']
        candidates = [name for name in candidates if FUNCT7.get(name) == f7]
    return candidates[0] if candidates else 'UNKNOWN'
