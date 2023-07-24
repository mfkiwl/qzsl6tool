#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libqznma.py: library for decoding QZNMA
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Signal Authentication Service,
#     IS-QZSS-SAS-001 Draft-002, Jan. 24, 2023.

import sys
import gps2utc
import libcolor
import libssr
try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

class Qznma:
    "Quasi-Zenith Satellite navigation authentication  message process class"
# --- private
    def __init__(self, fp_disp, t_level, color):
        self.fp_disp = fp_disp
        self.t_level = t_level
        self.msg_color = libcolor.Color(fp_disp, color)
        self.rds1 = bitstring.BitArray()
        self.rds2 = bitstring.BitArray()

# --- public
    def decode(self, payload):
        '''decode reformat digital signature (RDS) in L6E
        [1] p.67 Fig.6-52, 6-53, and 6-54'''
        if len(payload) != 1695:
            raise(f"QZNMA size error: {len(payload)} != 1695.")
        pos = 0
        rds1 = bitstring.BitArray(payload[pos:pos+576])
        pos += 576
        rds2 = bitstring.BitArray(payload[pos:pos+576])
        pos += 576
        reserved = bitstring.BitArray(payload[pos:pos+543])
        if '0b1' in reserved:
            self.trace(2, f"QZNMA dump: {reserved.bin}")
        message = ''
        message += self.decode_rds(rds1)
        message += self.decode_rds(rds2)
        return message

# --- private
    def trace(self, level, *args):
        if self.t_level < level:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def decode_rds(self, rds):
        '''decodes reformat digital signature
        [1] p.43 Table 6-2 GPS LNAV RDS Message
        '''
        pos = 0
        nma_id = rds[pos:pos+4]; pos += 4
        rtow   = rds[pos:pos+20].uint; pos += 20
        svid   = rds[pos:pos+8].uint; pos += 8
        mt     = rds[pos:pos+4].uint; pos += 4
        refeph = rds[pos:pos+4].uint; pos += 4
        keyid  = rds[pos:pos+8].uint; pos += 8
        signat = rds[pos:pos+512]; pos += 512
        salt   = rds[pos:pos+16].uint; pos += 16
        message = ''
        if nma_id != 0b0:
            if '0b1' in rds[4:]:
                message += f'QZNMA non null {rds[4:]}\n'
            return message
        message += f'\nQZNMA RefTOW={rtow} '
        if     1 <= svid and svid <= 63:
            message += f'G{svid:2d} '
        elif  65 <= svid and svid <= 127:
            message += f'E{svid-64:2d} '
        elif 129 <= svid and svid <= 191:
            message += f'S{svid:3d} '
        elif 193 <= svid and svid <= 202:
            message += f'J{svid-192:2d} '
        else:
            message += f'SVID={svid} '
        if   mt == 0b0001: message += 'LNAV '
        elif mt == 0b0010: message += 'CNAV '
        elif mt == 0b0011: message += 'CNAV2 '
        elif mt == 0b0100: message += 'F/NAV '
        elif mt == 0b0101: message += 'I/NAV '
        else:              message += 'unknown-NAV '
        message += f'RefEph={refeph} KeyID={keyid} salt={salt}\n'
        message += f'QZNMA signature={signat.bin}'
        return message

# EOF