#utils.py
#This file is for keeping binary number manipulation functions and all the decoding functions

from isa import OPCODES, FUNCT3, FUNCT7

# -----------------------------------------------------------------------------
#Bit Manipulation
# -----------------------------------------------------------------------------

def getBits(value : int, hi : int, lo : int) -> int:
    """
    Return bits from 'hi' to 'lo' in the binary representation of 'value'
    """
    value = value >> lo
    mask = (1 << (hi - lo + 1)) - 1
    value = value & mask
    return value

def signExtend(value : int, bits: int) -> int:
