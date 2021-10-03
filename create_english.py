#!/usr/bin/env python3

import re
import csv
import shutil
import os
import libexe


'''
Take the translated text and produce an english release.
'''

def find_mod_for_addr(exe, addr):
    for m in exe.modules:
        start_addr = m.oldseg * 16
        offset = addr - start_addr
        if offset >= 0 and offset < m.datalen:
            return offset, m
    raise Exception("Could not find module for")

def produce_english_exe():

    with open("deutsch/FROSCH.EXE", "rb") as f:
        exe = libexe.read_exe(f)


    with open("english.csv", "r") as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')

        for row in spamreader:

            addr = int(row[0])
            strlen = row[1]
            german = row[2]
            english = row[3]

            if english == "TODO":
                continue

            mod_offset, mod = find_mod_for_addr(exe, addr)

                
            if strlen != 'X':

                if False:
                    strlen = int(strlen)
                        
                    english = english.replace("{UP}", "\x18")
                    english = english.replace("{DOWN}", "\x19")

                    strdata = english.encode("cp437")

                    if len(strdata) > strlen:
                        print(f"{exe_addr:05x}: '{german}' : TOO LONG: '{strdata}' : Actual: '{strdata[:strlen]}'")
                        strdata = strdata[:strlen]

                    strlen = len(strdata)
                    data[exe_addr] = strlen
                    data[exe_addr+1:exe_addr+1+strlen] = strdata
            else:
                # 'X' means we can use extra space
                strdata = english.encode("cp437")
                strlen = len(strdata)
                mod.data[mod_offset] = strlen
                mod.data[mod_offset+1:mod_offset+1+strlen] = strdata

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