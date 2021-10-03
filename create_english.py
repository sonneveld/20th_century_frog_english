#!/usr/bin/env python3

import csv
import shutil
import os
import libexe


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
    

def produce_english_exe():

    with open("deutsch/FROSCH.EXE", "rb") as f:
        exe = libexe.read_exe(f)

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

    with open("english/FROG.EXE", 'wb') as f:
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