#!/usr/bin/env python3

import re
import csv
import shutil
import os

'''
Take the translated text and produce an english release.
'''


with open("deutsch/FROSCH.EXE", "rb") as f:
    data = f.read()
data = bytearray(data)


overflow = 0

with open("english.csv", "r") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')

    for row in spamreader:

        addr = int(row[0])
        strlen = row[1]
        english = row[3]

        exe_addr = addr + 0xf70

        if english == "TODO":
            continue
    
        if strlen != 'X':
            strlen = int(strlen)
                
            english = english.replace("{UP}", "\x18")
            english = english.replace("{DOWN}", "\x19")

            if len(english) > strlen:
                print(f"{exe_addr:05x}: str '{english}' is too long. Will only see '{english[:strlen]}'")
                overflow += len(english) + 1

            # sometimes FROG assumes full string, so we always pad with spaces and not change length
            strdata = english.encode("cp437") + b" "*100
            strdata = strdata[:strlen]

            data[exe_addr+1:exe_addr+1+strlen] = strdata
        else:
            strdata = english.encode("cp437")
            strlen = len(strdata)
            data[exe_addr] = strlen
            data[exe_addr+1:exe_addr+1+strlen] = strdata



print('overflow:', overflow)

os.makedirs("english", exist_ok=True)

with open("english/FROG.EXE", 'wb') as f:
    f.write(data)

files = [
    'deutsch/FROG.DRV',
    'ENGFROG.INF',
    'deutsch/file_id.diz',
]

for fname in files:
    shutil.copy(fname, "english/")
