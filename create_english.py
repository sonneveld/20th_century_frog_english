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


with open("english.csv", "r") as csvfile:
    spamreader = csv.reader(csvfile, delimiter=',', quotechar='"')

    for row in spamreader:

        addr = int(row[0])
        strlen = int(row[1])
        english = row[3]

        exe_addr = addr + 0xf70

        if english == "TODO":
            continue
    
        # print (addr, strlen, english)
        if len(english) > strlen:
            print(f"str '{english}' is too long. Will only see '{english[:strlen]}'")

        strdata = english.encode("cp437") + b" "*100
        strdata = strdata[:strlen]
        # print(repr(strdata))

        data[exe_addr+1:exe_addr+1+strlen] = strdata


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
