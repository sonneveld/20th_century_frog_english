#!/usr/bin/env python3

import csv
import shutil
import os
import libexe
import subprocess


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
    instr = bytes([0xBF, mod_offset&0xFF, (mod_offset>>8)&0xFF, 0x0E, 0x57])
    new_instr = bytes([0xBF, str_offset&0xFF, (str_offset>>8)&0xFF, 0x0E, 0x57])

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

def fix_relocation(seg, offset, bin_length):
    for i in range(bin_length-1):
        if seg.data[offset+i] == 0xAD and seg.data[offset+i+1] == 0xDE:
            seg.data[offset+i] = 8
            seg.data[offset+i+1] = 0
            seg.relocations.append(offset + i)
            print(f"reloc: {offset + i:04x}")


def add_timer_patch(exe):

    timerpatch = nasm('timer.asm')

    # Add timer
    # 16BC:009A
    overrideset_9a = timerpatch[0x9a:0x9a+8]
    # 16BC:00f4
    overriderestore_f4 = timerpatch[0xf4:0xf4+11]

    seg7 = exe.modules[7]
    seg7.data[0x9a:0x9a+8] = overrideset_9a
    seg7.data[0xf4:0xf4+11] = overriderestore_f4


    offset = len(seg7.data)
    assert offset == 0x1da0
    intcode = bytearray(timerpatch[offset:offset+0x100])
    seg7.data.extend(intcode)
    seg7.datalen += len(intcode)
    fix_relocation(seg7, offset, len(intcode))


    gamelooppatch = nasm('gameloop.asm')

    seg0 = exe.modules[0]

    for offset in [0x3c97, 0x3d44, 0x3d71]:
        jmp_override = gamelooppatch[offset:offset+3]
        seg0.data[offset:offset+3] = jmp_override

    offset = len(seg0.data)
    assert offset == 0x3e10
    intcode = bytearray(gamelooppatch[offset:offset+0x100])
    seg0.data.extend(intcode)
    seg0.datalen += len(intcode)
    fix_relocation(seg0, offset, len(intcode))


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


def produce_english_exe():

    with open("deutsch/FROSCH.EXE", "rb") as f:
        exe = libexe.read_exe(f)

    add_timer_patch(exe)

    add_english_patch(exe)

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