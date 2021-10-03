#!/usr/bin/env python3

import os
import os.path
import struct


'''
References:
https://wiki.osdev.org/MZ
https://www.fileformat.info/format/exe/corion-mz.htm
https://moddingwiki.shikadi.net/wiki/EXE_Format
https://tuttlem.github.io/2015/03/28/mz-exe-files.html
'''

PARAGRAPH = 0x10
PAGE = 0x200

SEG_EXTRA_DATA = 1024


header_name_by_offset = [
    "Signature",
    "Extra Bytes",
    "Pages",
    "Relocation count",
    "Header size",
    "Min allocation",
    "Max allocation",
    "Initial SS",
    "Initial SP",
    "Checksum",
    "Initial IP",
    "Initial CS",
    "Relocation Offset",
    "Overlay",
    "Overlay Extra",
]


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def read_word(data, offset):
    return data[offset] | (data[offset+1]<<8)

def write_word(data, offset, value):
    data[offset] = value & 0xff
    data[offset+1] = (value >> 8) & 0xff



class Exe:

    def __init__(self, ss, sp, ip, cs, modules, post_data, seg_addrs):
        self.ss = ss
        self.sp = sp
        self.ip = ip
        self.cs = cs
        self.modules = modules
        self.post_data = post_data
        self.seg_addrs = seg_addrs

    def find_mod_for_addr(self, addr):
        for m in self.modules:
            start_addr = m.oldseg * 16
            offset = addr - start_addr
            if offset >= 0 and offset < m.olddatalen:
                return offset, m
        raise Exception("Could not find module for")

class Module:

    def __init__(self, data, datalen, relocations, oldseg):
        self.data = bytearray(data)
        self.datalen = datalen
        self.olddatalen = datalen
        self.relocations = relocations
        self.oldseg = oldseg

    def get_size_paragraphs(self):
        result, remainder = divmod(self.datalen, PARAGRAPH)
        if remainder > 0:
            result += 1
        return result


def read_exe(f):

    header = f.read(14*2)
    header = struct.unpack("<14H", header)
    for i, x in enumerate(header):
        print(f"{i*2:02x}: {header_name_by_offset[i]} : 0x{x:04x}")

    assert header[0] == 0x5a4d

    header_size = header[4] * PARAGRAPH

    last_page = header[1]
    exe_num_pages = header[2]
    if last_page == 0:
        exe_size = exe_num_pages * PAGE
    else:
        exe_size = (exe_num_pages - 1) * PAGE + last_page

    # min_alloc = header[5]
    # max_alloc = header[6]
    ss = header[7]
    sp = header[8]
    ip = header[10]
    cs = header[11]
    
    # process relocation table

    number_of_relocations = header[3]
    relocations_offset = header[12]
    f.seek(relocations_offset, os.SEEK_SET)
    relocations = f.read(number_of_relocations*4) # each entry is 2 words each
    relocations = struct.unpack(f"<{number_of_relocations*2}H", relocations)
    relocations = list(chunks(relocations, 2))

    relocations_addrs = []
    found_segs = set()

    found_segs.add(ss)
    found_segs.add(cs)

    for offset, segment in relocations:
        addr = offset + segment*PARAGRAPH
        relocations_addrs.append(addr)
        found_segs.add(segment)

    # read in whole exe

    f.seek(0, os.SEEK_SET)
    full_header_data = f.read(header_size)

    data = f.read(exe_size - header_size)
    assert len(data) == exe_size - header_size

    # sometimes there's bits left over.
    post_data = f.read()

    # collect non-adjusted segments
    for addr in relocations_addrs:
        v = data[addr] | (data[addr+1]<<8)
        found_segs.add(v)

    found_segs = list(sorted(found_segs))


    # split up segments

    modules = []

    for i, seg_start in enumerate(found_segs):

        start_addr = seg_start*16


        end_addr = None
        datalen = 0
        if i+1 < len(found_segs):
            end_addr = found_segs[i+1] * 16
            datalen = (found_segs[i+1] - seg_start) * 16

        segdata = bytearray(data[start_addr:end_addr])
        segment_relocations = [offset for offset,segment in relocations if segment == seg_start]
        modules.append(Module(segdata, datalen, segment_relocations, seg_start))


    # normalise segment offsets by converting to index
    
    for m in modules:
        for reloc_addr in m.relocations:
            old_v = read_word(m.data, reloc_addr)
            new_v = found_segs.index(old_v)
            write_word(m.data, reloc_addr, new_v)

    ss = found_segs.index(ss)
    cs = found_segs.index(cs)

    return Exe(ss, sp, ip, cs, modules, post_data, found_segs)



def write_exe(f, exe):

    # prepare program data
    program_data = bytearray()
    program_data_len = None

    module_segments = []

    for m in exe.modules:
        module_seg, remaining = divmod(len(program_data), 16)
        assert remaining == 0
        module_segments.append(module_seg)
        program_data.extend(m.data)

        padding_bytes = m.datalen - len(m.data)
        assert padding_bytes >= 0
        if padding_bytes:
            if program_data_len is None:
                program_data_len = len(program_data)
            program_data.extend( bytes([0]* padding_bytes))

        while len(program_data) % 16 != 0:
            program_data.append(0)

    if program_data_len is None:
        program_data_len = len(program_data)

    # patch program data
    for seg, m in zip(module_segments, exe.modules):
        for r in m.relocations:
            old_v = read_word(program_data, seg*16+r)
            new_v = module_segments[old_v]
            write_word(program_data, seg*16+r, new_v)

    # prepare header

    num_relocations = 0
    for m in exe.modules:
        num_relocations += len(m.relocations)

    header_size = 14*2 + num_relocations*4
    while header_size % 16 != 0:
        header_size += 1

    exe_size = header_size + program_data_len
    exe_size_pages, remaining = divmod(exe_size, 512)
    if remaining != 0:
        exe_size_pages += 1

    header_data = bytearray([0]*header_size)

    # bit of a fudge but seems to match
    alloc_size = (program_data_len * 2 + 4096) // 16

    write_word(header_data, 0, 0x5a4d) # MZ
    write_word(header_data, 2, remaining) # last page size
    write_word(header_data, 4, exe_size_pages) # num pages
    write_word(header_data, 6, num_relocations) # num relocations
    write_word(header_data, 8, header_size // 16) # header size
    write_word(header_data, 0xa, alloc_size) #  mem alloc min
    write_word(header_data, 0xc, alloc_size) #  mem alloc max
    write_word(header_data, 0xe, module_segments[exe.ss]) # adjusted ss
    write_word(header_data, 0x10, exe.sp) # sp
    write_word(header_data, 0x12, 0) # ignored checksum
    write_word(header_data, 0x14, exe.ip) # ip
    write_word(header_data, 0x16, module_segments[exe.cs]) # adjusted cs
    write_word(header_data, 0x18, 0x1c) # relocation offset
    write_word(header_data, 0x1A, 0) # overlay num

    # prepare relocation table
    offset = 0x1c
    for seg, m in zip(module_segments, exe.modules):
        for r in m.relocations:
            write_word(header_data, offset, r)
            offset += 2
            write_word(header_data, offset, seg)
            offset += 2

    # write it!!

    f.write(header_data)
    f.write(program_data[:program_data_len])
    f.write(exe.post_data)




if __name__ == "__main__":
    with open("deutsch/FROSCH.EXE", "rb") as f:
        exe = read_exe(f)

    if False:
        # TEST CODE
        exe.modules[0].data.extend( bytes([0]*42))
        exe.modules[0].datalen += 42

        exe.modules[1].data.extend( bytes([0]*66))
        exe.modules[1].datalen += 66

        exe.modules[2].data.extend( bytes([0]*88))
        exe.modules[2].datalen += 88

        exe.modules[3].data.extend( bytes([0]*99))
        exe.modules[3].datalen += 99

        exe.modules[4].data.extend( bytes([0]*422))
        exe.modules[4].datalen += 422

    with open("hacked.exe", "wb") as f:
        write_exe(f, exe)
