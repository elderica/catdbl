#!env python
# coding: utf-8

# Copyright (c) 2013 Kazuki Shigemichi <shigemichik@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to
# whom the Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import collections
import struct
import csv
import sys

fixed_header_parser = struct.Struct('<14s2s32s48s16sLHHHfH384s')
FixedHeader = collections.namedtuple('FixedHeader', [
    'filetype',
    'start_attr',
    'title',
    'start_time',
    'unused',
    'data_size',
    'spare',
    'channel_size',
    'sampling_freq',
    'sampling_time',
    'lag',
    'system'
    ])

variable_header_parser = struct.Struct('<32s8sfLfLLLL28s')
VariableHeader = collections.namedtuple('VariableHeader', [
    'channel_comment',
    'unit',
    'full_scale',
    'calibration',
    'physical_amount_cf',
    'unused',
    'zero_offset',
    'max',
    'min',
    'spare'
    ])

ParsedTarget = collections.namedtuple('ParsedTarget', [
    'fixed_header',
    'variable_headers',
    'data_valuess'
    ])

data_value_reader = struct.Struct('<H')

def parse(fp):
    fheader_s = fp.read(512)
    fixed_header = FixedHeader._make(
        fixed_header_parser.unpack(fheader_s))

    ch_size = fixed_header.channel_size
    d_size = fixed_header.data_size

    vheaders = []
    dvaluess = []

    for i in range(ch_size):
        vheaders.append(VariableHeader._make(
            variable_header_parser.unpack(fp.read(96))))

    for i in range(d_size):
        line_dvalues = []
        for ch in range(ch_size):
            line_dvalues.append(
                data_value_reader.unpack(fp.read(2))[0])
        dvaluess.append(line_dvalues)

    return ParsedTarget._make((fixed_header, vheaders, dvaluess))

def csv_print(pt, fp):
    out = csv.writer(fp)
    out.writerow([pt.fixed_header.title])
    out.writerow([t.channel_comment.strip() for t in pt.variable_headers])
    for dvs in pt.data_valuess:
        epairs = zip([ch.physical_amount_cf for ch in pt.variable_headers], dvs)
        out.writerow(['%9.4E' % (p[0]*p[1],) for p in epairs])        

def main():
    if len(sys.argv) > 1:
        fp = file(sys.argv[1], 'rb')
    else:
        fp = sys.stdin

    pt = parse(fp)
    csv_print(pt, sys.stdout)

    fp.close()

if __name__ == '_main__':
    pass
