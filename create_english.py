#!/usr/bin/env python3

import csv
import shutil
import os
import libexe
import subprocess

from endian import read_le_word, write_le_word

OP_NOP = 0x90
OP_JMP_REL16 = 0xeb
OP_MOV_DI_IMM = 0xBF 
OP_PUSH_CS = 0x0E
OP_PUSH_DI = 0x57

'''
Take the translated text and produce an english release.
'''

def replace_big_string(mod, mod_offset, strdata):

    print(f"Doing magic for str {repr(strdata)}")

    pascal_str = bytearray()
    pascal_str.append(len(strdata))
    pascal_str.extend(strdata)

    str_offset = mod.datalen

    mod.data.extend(pascal_str)
    mod.datalen += len(pascal_str)

    # instructions for mov di, offset ; push cs ; push di
    instr = bytes([OP_MOV_DI_IMM, mod_offset&0xFF, (mod_offset>>8)&0xFF, OP_PUSH_CS, OP_PUSH_DI])
    new_instr = bytes([OP_MOV_DI_IMM, str_offset&0xFF, (str_offset>>8)&0xFF, OP_PUSH_CS, OP_PUSH_DI])

    replace_count = 0
    while True:
        instr_offset = mod.data.find(instr)
        if instr_offset < 0:
            break
        mod.data[instr_offset:instr_offset+len(new_instr)] = new_instr
        replace_count += 1
    assert replace_count > 0
    
def hex_to_bytes(hexstr):
    '''
    Take a hex string like "0a 0b 0c 0d" and return a bytes obj
    '''
    tokens = hexstr.split()
    hexbytes = bytes([int(x,16) for x in tokens])
    return hexbytes

def nasm(asmfile):
    basename, _ = os.path.splitext(asmfile)
    binpath = basename + ".bin"
    subprocess.run(['nasm', asmfile, '-o', binpath], check=True)
    with open(binpath, 'rb') as f:
        asmbin = f.read()
    return asmbin

def fix_relocation_to_dataseg(seg, offset, bin_length):
    for i in range(bin_length-1):
        if read_le_word(seg.data, offset+i) == 0xDEAD:
            write_le_word(seg.data, offset+i, 0)
            assert offset not in seg.seg_index_for_offset
            seg.seg_index_for_offset[offset+i] = 8
            print(f"reloc: {offset + i:04x}")


def add_timer_patch(exe):

    # CHAIN TIMER TO KEEP TRACK OF TIME
    print("..timer")
    timerpatch = nasm('timer.asm')

    # Add timer
    seg7 = exe.modules[7]
    # set and restore timer int, replaces a debug int
    for offset, patchlen in [(0x9a, 8), (0xf4, 11)]:
        patchbin = timerpatch[offset:offset+patchlen]
        seg7.data[offset:offset+patchlen] = patchbin

    offset = len(seg7.data)
    assert offset == 0x1da0
    intcode = bytearray(timerpatch[offset:offset+0x100])
    seg7.data.extend(intcode)
    seg7.datalen += len(intcode)
    fix_relocation_to_dataseg(seg7, offset, len(intcode))


    # MODIFY DELAY
    '''
    Using the new timer (added above), replace the cpu calibrated
    delay function with one that waits for the number of ticks.
    This fixes issues on fast cpus.
    '''
    print("..delay")
    seg6 = exe.modules[6]
    delaypatch = nasm('delay.asm')
    for offset, patchlen in [(0x2e9, 0x10), ]:
        patchbin = delaypatch[offset:offset+patchlen]
        seg6.data[offset:offset+patchlen] = patchbin
    
    offset = len(seg6.data)
    assert offset == 0x660
    intcode = bytearray(delaypatch[offset:offset+0x100])
    seg6.data.extend(intcode)
    seg6.datalen += len(intcode)
    fix_relocation_to_dataseg(seg6, offset, len(intcode))



    # ADD VSYNC AND DELAY TO GAMELOOP
    '''
    The original gameloop had multiple delays, depending on how much
    was rendered on the screen. Unloaded, the game loop waited about
    21ms which is about 48Hz. If we take into account rendering, it
    might have slowed down to about 30-35Hz, which is what we will 
    replace the delay with.
    '''
    print("..gameloop")
    gamelooppatch = nasm('gameloop.asm')

    seg0 = exe.modules[0]

    # disable original gameloop delays
    delays_to_skip = [ 
        (0x3db, 0x3e4), 
        (0x413, 0x41c),  
        (0x1844, 0x184d),
        (0x1902, 0x190b),
        (0x1912, 0x191b),
        (0x191b, 0x1924),
        (0x196e, 0x1977),
        (0x19e4, 0x19ed),
        (0x1a4c, 0x1a55),
        (0x1ab6, 0x1abf),
        (0x1cf1, 0x1cfa),
        (0x239d, 0x23a5),
    ]
    if False:
        # old method, skip over code with jump
        for offset_begin, offset_end in delays_to_skip:
            jmp_rel = offset_end - offset_begin - 2
            seg0.data[offset_begin] = OP_JMP_REL16
            seg0.data[offset_begin+1] = jmp_rel
    else:
        for offset_begin, offset_end in delays_to_skip:
            for offset in range(offset_begin, offset_end):
                seg0.data[offset] = OP_NOP
                if offset in seg0.seg_index_for_offset:
                    del seg0.seg_index_for_offset[offset]
                    print(f"reloc del: 0000:0x{offset:04x}")

    for offset, patchlen in [(0x3c97,3), (0x3d44,3), (0x3d71,3)]:
        patchbin = gamelooppatch[offset:offset+patchlen]
        seg0.data[offset:offset+patchlen] = patchbin

    offset = len(seg0.data)
    assert offset == 0x3e10
    intcode = bytearray(gamelooppatch[offset:offset+0x100])
    seg0.data.extend(intcode)
    seg0.datalen += len(intcode)
    fix_relocation_to_dataseg(seg0, offset, len(intcode))


    # ADD VSYNC AND DELAY TO CREDITS
    '''
    The credits have no delay at all! It relies primarily on rendering
    being slow enough for a reasonable scroll. This just adds a 35Hz
    delay
    '''
    print("..credits+intro")
    creditspatchbin = nasm('credits.asm')
    seg1 = exe.modules[1]

    for offset, patchlen in [ (0x3eb7,3), (0x3ecb,3), (0x3f71, 4)]:
        patchbin = creditspatchbin[offset:offset+patchlen]
        seg1.data[offset:offset+patchlen] = patchbin

    offset = len(seg1.data)
    assert offset == 0x4210
    intcode = bytearray(creditspatchbin[offset:offset+0x100])
    seg1.data.extend(intcode)
    seg1.datalen += len(intcode)
    fix_relocation_to_dataseg(seg1, offset, len(intcode))


    # exta room for our data
    seg8 = exe.modules[8]
    seg8.datalen += 16


def add_english_patch(exe):

    with open("english.csv", "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')

        for row in csvreader:

            addr = int(row[0])
            strlen = row[1]
            german = row[2]
            english = row[3]

            if english == "TODO":
                continue

            mod_offset, mod = exe.find_mod_for_addr(addr)

            english = english.replace("{UP}", "\x18")
            english = english.replace("{DOWN}", "\x19")

            strdata = english.encode("cp437")

            # 'X' means we can use extra space
            if strlen == 'X' or len(strdata) <= int(strlen):
                if strlen != 'X':
                    assert mod.data[mod_offset] == int(strlen)
                newstrlen = len(strdata)
                mod.data[mod_offset] = newstrlen
                mod.data[mod_offset+1:mod_offset+1+newstrlen] = strdata
            else:
                replace_big_string(mod, mod_offset, strdata)

    # replace cmp al,'J' with 'Y'
    offset = exe.modules[0].data.find(b"\x3c\x4a")
    assert offset != -1
    exe.modules[0].data[offset:offset+2] = b'\x3c\x59'

    offset = exe.modules[1].data.find(b"\x3c\x4a")
    assert offset != -1
    exe.modules[1].data[offset:offset+2] = b'\x3c\x59'

def add_999_lives_patch(exe):
    # 999 lives edition
    dataseg = exe.modules[8]
    dataseg.data[0x1f26] = 0xe7
    dataseg.data[0x1f27] = 0x03

def enable_debug_keys(exe):
    '''
    The code for the debug keys is already in the binary, but there's
    a block of code that explicitly disables it. All this does is 
    replace that with nops.
    '''
    seg0 = exe.modules[0]
    for offset in range(0x24da, 0x24e9):
        seg0.data[offset] = OP_NOP
        if offset in seg0.seg_index_for_offset:
            del seg0.seg_index_for_offset[offset]
            print(f"reloc del: 0000:0x{offset:04x}")

def produce_english_exe():

    with open("deutsch/FROSCH.EXE", "rb") as f:
        exe = libexe.read_exe(f)

    add_timer_patch(exe)

    add_english_patch(exe)

    # enable_debug_keys(exe)

    with open("english/FROG.EXE", 'wb') as f:
        libexe.write_exe(f, exe)

    add_999_lives_patch(exe)

    with open("english/FROG999.EXE", 'wb') as f:
        libexe.write_exe(f, exe)


def create_english_release():

    os.makedirs("english", exist_ok=True)

    produce_english_exe()

    files = [
        'deutsch/FROG.DRV',
        'ENGFROG.INF',
        'deutsch/file_id.diz',
    ]

    for fname in files:
        shutil.copy(fname, "english/")


if __name__ == '__main__':
    create_english_release()