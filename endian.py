#!/usr/bin/env python3

def read_le_word(data, offset):
    return data[offset] | (data[offset+1]<<8)

def write_le_word(data, offset, value):
    data[offset] = value & 0xff
    data[offset+1] = (value >> 8) & 0xff
