#!/usr/bin/env python3

import re
import csv

''' 
Extract german strings from FROSCH.EXE by using the addresses of any
strings defined in frosch.idc .

Saves to file deutsch.csv

Produce in IDA Pro with "File > Produce File > Dump database to IDC file"
'''

with open("deutsch/FROSCH.EXE", "rb") as f:
    data = f.read()

str_addrs = []

with open("frosch.idc",encoding='cp437') as f:
    for l in f:
        l = l.strip()

        m = re.search("MakeStr\s*\((.*)\)", l)
        if m:
            tokens = [x.strip() for x in m.group(1).split(",")]
            tokens = [int(x, 16) for x in tokens]
            str_addrs.append(tokens[0])
        m = re.search("MakeName\s*\((.*)\)", l)
        if m:
            tokens = [x.strip() for x in m.group(1).split(",")]
            tokens[0] = int(tokens[0], 16)


with open('frosch.csv', 'w', newline='') as csvfile:
        
    spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)

    for addr in str_addrs:

        origaddr = addr

        addr += 0xf70

        strlen = data[addr]
        strval = data[addr+1:addr+1+strlen]
        strval = strval.decode('cp437')
        spamwriter.writerow([origaddr, strlen, strval, "TODO"])
