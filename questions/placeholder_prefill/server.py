import random
import string
import math

def generate(data):
    len_reg = 8
    ops = {
        'add': lambda x, y: x + y,
        'sub': lambda x, y: x - y,
        'and': lambda x, y: x & y,
        'or' : lambda x, y: x | y,
        'xor': lambda x, y: x ^ y,
        'nor': lambda x, y: (x ^ 0xffffffff) & (y ^ 0xffffffff)
    }
    #initialize register file
    reg_file = [0x00] * len_reg
    placeholders = [0] * len_reg
    placeholders[0] = formatHex(reg_file[0])
    for ii in range(1, len(reg_file)):
        reg_file[ii] = random.randint(0x00, 0x4f)
        placeholders[ii] = formatHex(reg_file[ii])
    data["params"]["placeholder"] = placeholders

    for ii in range(3):
        #choose random operation and random source and destination registers
        #PLEASE ADD GUARANTEED DEPENDENCIES!
        op = list(ops.keys())[random.randint(0, len(ops)-1)]

        regW = random.randint(0, len_reg-1)
        regR0 = random.randint(0, len_reg-1)
        regR1 = random.randint(0, len_reg-1)

        #format instruction to send to html
        data["params"]["inst"+str(ii)] = f"{op} ${regW}, ${regR0}, ${regR1}"

        #update the register file 
        opFunc = ops[op]
        reg_file[regW] = opFunc(reg_file[regR0], reg_file[regR1])
        if reg_file[regW] < 0:
            reg_file[regW] = 0xffffffff + reg_file[regW] + 0x1
        reg_file[0] = 0x00

    answers = [0] * len_reg
    for ii in range(len_reg):
        answers[ii] = (formatHex(reg_file[ii]))

    return data

def formatHex(hexVal):
    return "{0:#0{1}x}".format(hexVal, 10)
