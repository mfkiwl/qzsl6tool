#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# galinavead.py: Galileo I/NAV message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2023-2024 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Europe Union Agency for the Space Programme,
#     Galileo Open Service Signal-in-Space Interface Control
#     Document (OS SIS ICD), Issue 2.1 Nov. 2023.
# [2] Europe Union Agency for the Space Programme,
#     GALILEO Timing Service Message Operatioal Status Definition
#     (TSM OSD), Issue 1.0, Apr. 2024.
#     https://www.gsc-europa.eu/sites/default/files/sites/all/files/Galileo_Timing_Service_Message_Operational_Status_Definition_document_(TSM_OSD).pdf

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libnav
import libgnsstime
import libtrace
from   rtcmread import rtk_crc24q

try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    The code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

LEN_INAV = 228  # the bit length of I/NAV message
TSM_STAT_GST = [  # ref.[2], Table 6 and Table 3
    "Not OK",
    "Timing Service Level 1 (max tolerable error of 1000 ns)",
    "Timing Service Level 2 (max tolerable error of 100 ns)",
    "Reserved for Timing Service Level 3 (max tolerable error of 15 ns)",
    "Spare", "Spare", "Spare",
    "Monitoring not available",
]
TSM_STAT_UTC = [  # ref.[2], Table 7 and Table 4
    "Not OK",
    "Timing Service Level 1 (max tolerable error of 1000 ns)",
    "Timing Service Level 2 (max tolerable error of 100 ns)",
    "Reserved for Timing Service Level 3 (max tolerable error of 30 ns)",
    "Spare", "Spare", "Spare",
    "Monitoring not available",
]

def modtime_from_wt_ssp(wt, ssp):
    ''' returns estimated GST mod 30 (odd seconds) from the combination of
        the word type (wt) and the ssp. if estimation is unable, returns -1
        wt: word type 0-63
        ssp: secondary synchronization pattern, 04, 2b, 2f, or 00 (no ssp)
    '''
    if ssp.hex == '04':  # SSP1
        if wt ==  2: return  1
        if wt ==  7: return  7
        if wt ==  9: return  7
        if wt == 19: return 13
        if wt == 20: return 13
        if wt == 22: return 19
        if wt ==  0: return 19  # when ARAIM is not available
        if wt ==  5: return 25
    if ssp.hex == '2b':  # SSP2
        if wt ==  4: return  3
        if wt ==  8: return  9
        if wt == 10: return  9
        if wt == 16: return 15
        if wt ==  1: return 21
        if wt ==  0: return 27
    if ssp.hex == '2f':  # SSP3
        if wt ==  6: return  5
        if wt == 17: return 11
        if wt == 18: return 11
        if wt ==  0: return 17
        if wt ==  3: return 23
        if wt == 16: return 29
    return -1

def decode_word1(df, nav, svid):
    ''' decodes word 1 and modifies ephemeris e
    '''
    e = nav.eph[svid-1]   # ephemeris for the satellite svid
    e.iodn = df.read(10)  # issue of data - nav
    e.t0e  = df.read(14)  # t0e
    e.m0   = df.read(32)  # m0
    e.e    = df.read(32)  # e
    e.a12  = df.read(32)  # sqrt(A)
    df.pos += 2           # reserved

def decode_word2(df, nav, svid):
    ''' decodes word 2 and modifies ephemeris e
    '''
    e = nav.eph[svid-1]   # ephemeris for the satellite svid
    e.iodn = df.read(10)  # issue of data - nav
    e.omg0 = df.read(32)  # omg0
    e.i0   = df.read(32)  # i0
    e.omg  = df.read(32)  # omg
    e.idot = df.read(14)  # idot
    df.pos += 2           # reserved

def decode_word3(df, nav, svid):
    ''' decodes word 3 and modifies ephemeris e
    '''
    e = nav.eph[svid-1]   # ephemeris for the satellite svid
    e.iodn = df.read(10)  # issue of data - nav
    e.omgd = df.read(24)  # omgd
    e.dn   = df.read(16)  # delta_n
    e.cuc  = df.read(16)  # cuc
    e.cus  = df.read(16)  # cus
    e.crc  = df.read(16)  # crc
    e.crs  = df.read(16)  # crs
    e.se5b = df.read( 8)  # SISA(E1, E5b)

def decode_word4(df, nav, svid):
    ''' decodes word 4 and modifies ephemeris e
    '''
    e = nav.eph[svid-1]    # ephemeris for the satellite svid
    e.iodn  = df.read(10)  # issue of data - nav
    e.svid4 = df.read( 6)  # SVID
    e.cic   = df.read(16)  # cic
    e.cis   = df.read(16)  # cis
    e.t0c   = df.read(14)  # t0c
    e.af0   = df.read(31)  # af0
    e.af1   = df.read(21)  # af1
    e.af2   = df.read( 6)  # af2
    df.pos += 2            # spare

def decode_word5(df, nav, svid):
    ''' decodes word 5 and modifies ephemeris e
    '''
    e = nav.eph[svid-1]     # ephemeris for the satellite svid
    e.ai0  = df.read(11)    # a_i0
    e.ai1  = df.read(11)    # a_i1
    e.ai2  = df.read(14)    # a_i2
    e.idf  = df.read( 5)    # Ionosheric disturbance flag region
    e.be5a = df.read(10)    # BGD(E1, E5a)
    e.be5b = df.read(10)    # BGD(E1, E5b)
    e.e5h  = df.read( 2)    # E5b health
    e.e1h  = df.read( 2)    # E1B health
    e.e5v  = df.read( 1)    # E5b DVS
    e.e1v  = df.read( 1)    # E1B DVS
    nav.wn   = df.read(12)  # week number
    nav.tow  = df.read(20)  # time of week
    df.pos += 23            # spare

def decode_word6(df, nav):
    ''' decodes word 6 and modifies ephemeris e
    '''
    nav.a0    = df.read(32)  # A0
    nav.a1    = df.read(24)  # A1
    nav.dtls  = df.read( 8)  # dt_LS
    nav.t0t   = df.read( 8)  # t_ot
    nav.wn0t  = df.read( 8)  # WN_0t
    nav.wnlsf = df.read( 8)  # WN_LSF
    nav.dn    = df.read( 3)  # DN
    nav.dtlsf = df.read( 8)  # dt_LSF1
    nav.tow   = df.read(20)  # time of week
    df.pos += 3              # spare

def decode_word7(df, nav):
    ''' decodes word 7 and modifies almanac nav
    '''
    nav.ioda  = df.read( 4)    # issue of data - almanac
    nav.wna   = df.read( 2)    # week number almanac
    nav.t0a   = df.read(10)    # t_0a
    nav.svid1 = df.read( 6).u  # SVID1
    a1 = nav.alm[nav.svid1-1]  # almanac for SVID1
    a1.da12 = df.read(13)      # d_sqrt(A)
    a1.e    = df.read(11)      # e
    a1.omg  = df.read(16)      # omg
    a1.di   = df.read(11)      # delta_i
    a1.omg0 = df.read(16)      # omg0
    a1.omgd = df.read(11)      # omgd
    a1.m0   = df.read(16)      # m0

def decode_word8(df, nav):
    ''' decodes word 8 and modifies almanac nav
    '''
    nav.ioda = df.read( 4)         # issue of data - almanac
    if nav.svid1 == -1:            # if the almanac for SVID1 is not available
        df.pos += 16 + 13 + 2 + 2  # skip reading almanac for SVID1
    else:
        a1 = nav.alm[nav.svid1-1]  # almanac for SVID1
        a1.af0  = df.read(16)      # af0
        a1.af1  = df.read(13)      # af1
        a1.e5h  = df.read( 2)      # E5b health
        a1.e1h  = df.read( 2)      # E1B health
    nav.svid2  = df.read( 6).u     # SVID2
    a2 = nav.alm[nav.svid2-1]      # almanac for SVID2
    a2.da12 = df.read(13)          # d_sqrt(A)
    a2.e    = df.read(11)          # e
    a2.omg  = df.read(16)          # omg
    a2.di   = df.read(11)          # delta_i
    a2.omg0 = df.read(16)          # omg0
    a2.omgd = df.read(11)          # omgd
    df.pos += 1                    # spare

def decode_word9(df, nav):
    ''' decodes word 9 and modifies almanac nav
    '''
    nav.ioda = df.read( 4)     # issue of data - almanac
    nav.wna  = df.read( 2)     # week number almanac
    nav.t0a  = df.read(10)     # t_0a
    if nav.svid2 == -1:        # if the almanac for SVID2 is not available
        df.pos += 16 + 16 + 13 + 2 + 2  # skip reading almanac for SVID2
    else:
        a2 = nav.alm[nav.svid2.u-1]   # almanac for SVID2
        a2.m0  = df.read(16)   # m0
        a2.af0 = df.read(16)   # af0
        a2.af1 = df.read(13)   # af1
        a2.e5h = df.read( 2)   # E5b health
        a2.e1h = df.read( 2)   # E1B health
    nav.svid3 = df.read( 6).u  # SVID3
    a3 = nav.alm[nav.svid3-1]  # almanac for SVID3
    a3.da12 = df.read(13)      # d_sqrt(A)
    a3.e    = df.read(11)      # e
    a3.omg  = df.read(16)      # omg
    a3.di   = df.read(11)      # delta_i

def decode_word10(df, nav):
    ''' decodes word 10 and modifies almanac nav
    '''
    nav.ioda = df.read( 4)           # issue of data - almanac
    if nav.svid3 == -1:              # if the almanac for SVID3 is not available
        df.pos += 16 + 11 + 16 + 16 + 13 + 2 + 2  # skip reading almanac for SVID3
    else:
        a3 = nav.alm[nav.svid3.u-1]  # almanac for SVID3
        a3.omg0 = df.read(16)        # omg0
        a3.omgd = df.read(11)        # omgd
        a3.m0   = df.read(16)        # m0
        a3.af0  = df.read(16)        # af0
        a3.af1  = df.read(13)        # af1
        a3.e5h  = df.read( 2)        # E5b health
        a3.e1h  = df.read( 2)        # E1B health
    nav.a0g  = df.read(16)           # A_0G
    nav.a1g  = df.read(12)           # A_1G
    nav.t0g  = df.read( 8)           # t_0G
    nav.wn0g = df.read( 6)           # WN_0G

def decode_word16(df, nav, svid):
    ''' decodes reduced CED 
    '''
    e = nav.eph[svid-1]   # ephemeris for the satellite svid
    e.da   = df.read( 5)  # delta_A
    e.ex   = df.read(13)  # e_x
    e.ey   = df.read(13)  # e_y
    e.di0  = df.read(17)  # delta i_0
    e.omg0 = df.read(23)  # omg0
    e.l0   = df.read(23)  # lambda0
    e.af0  = df.read(22)  # af0
    e.af1  = df.read( 6)  # af1

def decode_fec2(df, nav, wt):
    ''' returns decoded values
    '''
    if wt == 17:
        nav.ced1  = df.read(  8)  # Reed-Solomon for CED 1
        nav.iodnl = df.read(  2)  # IODnav LSB
        nav.ced2  = df.read(112)  # Reed-Solomon for CED 2
    elif wt == 18:
        nav.ced3  = df.read(  8)
        nav.iodnl = df.read(  2)
        nav.ced4  = df.read(112)
    elif wt == 19:
        nav.ced5  = df.read(  8)
        nav.iodnl = df.read(  2)
        nav.ced6  = df.read(112)
    elif wt == 20:
        nav.ced7  = df.read(  8)
        nav.iodnl = df.read(  2)
        nav.ced8  = df.read(112)
    else:
        raise Exception(f"word type for FEC2 should be either 17, 18, 19, 20 ({wt})")

def decode_word0(df, nav):
    ''' returns decoded values
    '''
    nav.time  = df.read( 2)  # time
    nav.spare = df.read(88)  # spare
    nav.wn    = df.read(12)  # week number
    nav.tow   = df.read(20)  # time of week

def decode_word22(df, nav):
    ''' returns decoded message
        I/NAV ARAIM integrity support message (ISM), ref.[1], sect.4.3.7
    '''
    nav.gnss_id  = df.read( 3)  # GNSS constellation ID
    nav.gnss_ism = df.read(87)  # specific ISM content
    nav.crc      = df.read(32)  # ISM CRC
    if   nav.gnss_id.u == 0:    # test ISM I/NAV
        libtrace.info(f"Test gnss_ism={(nav.gnss_ism + bitstring.Bits(1)).hex} crc={nav.crc.hex}")
        return
    elif nav.gnss_id.u != 1:          # not Galileo
        libtrace.info(f"gnss_id={nav.gnss_id} gnss_ism={(nav.gnss_ism + bitstring.Bits(1)).hex} crc={nav.crc.hex}")
        return
    nav.slid = e.gnss_ism.read(3).u   # service level ID
    ism  = nav.gnss_ism.read( 84 )    # integrity support message content
    if   nav.slid == 0:               # service level 1
        msg = f"GAL level={e.slid+1} spare={ism.hex} crc={e.crc.hex}"
    elif nav.slid == 2:               # service level 3
        nav.wn      = ism.read(12)    # WN_ISM
        nav.t0      = ism.read( 9)    # t0_ISM
        nav.maskmsb = ism.read( 1)    # mask - MSB
        nav.mask    = ism.read(32)    # mask
        nav.pconst  = ism.read( 4)    # P_const
        nav.psat    = ism.read( 4)    # P_sat
        nav.ura     = ism.read( 4)    # URA
        nav.ure     = ism.read( 4)    # URE
        nav.bnom    = ism.read( 4)    # b_nom
        nav.tv      = ism.read( 4)    # t_validity
        ism.pos += 6                  # spare
        msg = f"GAL level=3 wn={nav.wn.u} t0={nav.t0.u} maskmsb={nav.maskmsb.u} mask={nav.mask.u} pconst={nav.pconst.u} psat={nav.psat.u} ura={nav.ura.u} ure={nav.ure.u} bnom={nav.bnom.u} tv={nav.tv.u}"
    else:                           # other service level
        msg = f"GAL level={nav.slid+1} ism={ism.hex} crc={nav.crc.hex}"
    libtrace.info(msg)

def decode_word44(df, nav):
    ''' returns decoded message
        Galileo Timing Service Message, ref.[2], Table 5 (p.5)
    '''
    msg = f"GST service level:"
    nav.sl = [0 for _ in range(37)]
    for svid in range(36):
        sl = df.read(3).u
        nav.sl[svid] = sl
        msg += f'\nE{svid+1:02d}: {TSM_STAT_GST[sl]}'
    sl = df.read(3).u
    nav.sl[36] = sl
    msg += f'\nUTC: {TSM_STAT_UTC[sl]}'
    libtrace.info(msg)

def decode_word63():
    ''' returns decoded message
    '''
    pass

class GalInav:
    sar_sl     = [0 for _ in range(libnav.N_GALSAT)]  # SAR (search and rescue) short/long identifier
    sar_part   = [0 for _ in range(libnav.N_GALSAT)]  # SAR part number, 0=not ready
    sar_code   = [0 for _ in range(libnav.N_GALSAT)]  # SAR message code
    sar_beacon = [bitstring.BitStream() for _ in range(libnav.N_GALSAT)]  # SAR data
    sar_param  = [bitstring.BitStream() for _ in range(libnav.N_GALSAT)]  # SAR parameter

    def __init__(self, trace):
        self.trace = trace
        self.nav  = libnav.NavGal(trace)  # navigation messages

    def decode_inav(self, svid, inav):
        ''' returns decoded message
            svid: 1-36
            inav: 228-bit long
        '''
        eo1   = inav.read(  1)  # Even/Odd, should be 0 (even)
        pt1   = inav.read(  1)  # page type, should be 0 (normal)
        df1   = inav.read(112)  # data 1/2
        eo2   = inav.read(  1)  # Even/Odd, should be 1 (odd)
        pt2   = inav.read(  1)  # page type, should be 0 (normal)
        df2   = inav.read( 16)  # data 2/2
        osnma = inav.read( 40)  # OSNMA (open service navigation message authentication)
        sar   = inav.read( 22)  # SAR (search and rescue)
        inav.pos += 2           # spare
        crc   = inav.read( 24)  # CRC
        ssp   = inav.read(  8)  # SSP (secondary synchronization pattern)
        df    = df1 + df2       # data field
        wt    = df.read(6).u    # word type
        msg   = self.trace.msg(0, f'E{svid:02d} ', fg='green')
# --- secondary synchronization pattern (SSP) ---
        if    ssp.hex == '04': msg += self.trace.msg(0, 'SSP1 ', fg='cyan')
        elif  ssp.hex == '2b': msg += self.trace.msg(0, 'SSP2 ', fg='cyan')
        elif  ssp.hex == '2f': msg += self.trace.msg(0, 'SSP3 ', fg='cyan')
        elif  ssp.hex == '00': msg += '     '
        elif  ssp.hex == 'fd': msg += '     '
        else: msg += self.trace.msg(0, f'SSP? ({ssp.hex}) ', fg='red')
# --- data check ---
        frame = (bitstring.Bits('uint4=0') + inav[0:196]).tobytes()
        crc_frame = rtk_crc24q(frame, len(frame))
        if crc_frame != crc.tobytes():
            return msg + self.trace.msg(0, f'Word {wt:2d} CRC error: {crc_frame.hex()} != {crc.hex}', fg='red')
        if eo1.u != 0 or eo2.u != 1:
            return msg + self.trace.msg(0, 'Even/Odd page error', fg='red')
        if pt1.u or pt2.u:
            return msg + self.trace.msg(0, 'Alert page', fg='red')
# --- word type ---
        msg += self.trace.msg(0, f'Word {wt:2d} ', fg='yellow')
# --- estimated GST mod 30 ---
        modtime= modtime_from_wt_ssp(wt, ssp)
        msg += self.trace.msg(0, f'({modtime:02d}) ' if modtime != -1 else '     ', fg='magenta')
# --- message accumulation ---
        if   wt ==  1: decode_word1 (df, self.nav, svid)  # Ephemeris 1, ref.[1]
        elif wt ==  2: decode_word2 (df, self.nav, svid)  # Ephemeris 2, ref.[1]
        elif wt ==  3: decode_word3 (df, self.nav, svid)  # Ephemeris 3 and SISA, ref.[1]
        elif wt ==  4: decode_word4 (df, self.nav, svid)  # Ephemeris 4 and clock, ref.[1]
        elif wt ==  5: decode_word5 (df, self.nav, svid)  # Iono, BGD, health, GST, ref.[1]
        elif wt ==  6: decode_word6 (df, self.nav)        # GST-UTC param, ref.[1]
        elif wt ==  7: decode_word7 (df, self.nav)        # Almanac 1, ref.[1]
        elif wt ==  8: decode_word8 (df, self.nav)        # Almanac 2, ref.[1]
        elif wt ==  9: decode_word9 (df, self.nav)        # Almanac 3, ref.[1]
        elif wt == 10: decode_word10(df, self.nav)        # Almanac 4, GST-GPS param, ref.[1]
        elif wt == 16: decode_word16(df, self.nav, svid)  # reduced CED, ref.[1]
        elif wt in {17, 18, 19, 20}: decode_fec2(df, self.nav, wt)  # FEC2, ref.[1]
        elif wt ==  0: decode_word0 (df, self.nav)        # spare word, ref.[1]
        elif wt == 22: decode_word22(df, self.nav)        # ARAIM, ref.[1]
        elif wt == 44: decode_word44(df, self.nav)        # Timing service message, ref.[2]
        elif wt == 63: decode_word63()                    # dummy message, ref.[1]
        else:
            return msg + self.trace.msg(0, '(unknown word)', fg='red')
        if wt in {5, 0}:  # word 5 and word 0 include Galileo time
            msg += f" {libgnsstime.gps2utc(self.nav.wn.u, self.nav.tow.u, 'GAL')} ({self.nav.wn.u} {self.nav.tow.u})"
        elif wt == 6:
            msg += f" TOW={self.nav.tow.u}"
# --- open signal navigation message authentication (OSNMA) ---
        msg += self.decode_osnma(svid, osnma)
# --- search and rescue (SAR) ---
        msg += self.decode_sar(svid, sar)
        return msg

    def decode_osnma(self, svid, osnma):
        ''' not implemented
            open service navigation message authentication (OSNMA)
        '''
        return ''

    def decode_sar(self, svid, sar):
        ''' returns when there is a decoded message
            search and rescue (SAR), ref.[1], sect.4.3.8
        '''
        start = sar.read( 1)  # start indicator: 1=start, 0=continuation
        sl    = sar.read( 1)  # short/long identifier: 0=short, 1=long
        data  = sar.read(20)  # SAR return link message (RLM)
        if start.u:                       # the first message part
            self.sar_part  [svid] = 1     # part number: 0=not ready
            self.sar_sl    [svid] = sl.u  # store short/long identifier
            self.sar_beacon[svid] = data  # SAR first part is for beacon ID
            return ""                     # we cannot distinguish this is the first part or no message
        elif self.sar_part[svid] == 0:    # if SAR reception is not ready
            return ""
        if sl.u != self.sar_sl[svid]:     # disagreement in current and previous short/long ident.
            self.sar_part  [svid] = 0     # clear all states
            self.sar_sl    [svid] = sl.u
            self.sar_beacon[svid] = bitstring.BitStream()
            self.sar_param [svid] = bitstring.BitStream()
            return ""
        self.sar_part[svid] += 1
        msg = f"\nSAR E{svid:02d} {'long' if self.sar_sl else 'short'} part {self.sar_part[svid]}"
        if   self.sar_part[svid] <= 3:  # message part 2 and 3 is for beacon ID
            self.sar_beacon[svid] += data
            return msg
        elif self.sar_part[svid] == 4:  # message part 4 is for code and param.
            self.sar_code [svid] = data.read( 4).u  # message code
            self.sar_param[svid] = data.read(16)    # parameter
            if self.sar_sl[svid] == 0:  # SAR short message
                msg += f' beacon={self.sar_beacon[svid].hex} code={self.sar_code[svid]} param={self.sar_param[svid].hex}'
                self.sar_part  [svid] = 0  # clear all states
                self.sar_sl    [svid] = sl.u
                self.sar_beacon[svid] = bitstring.BitStream()
                self.sar_param [svid] = bitstring.BitStream()
            return msg
        self.sar_param[svid] += data  # message parts 5-8 are for parameter
        if self.sar_part[svid] < 8:   # SAR long message
            return msg
        msg += f' beacon={self.sar_beacon[svid].hex} code={self.sar_code[svid]} param={self.sar_param[svid].hex}'
        self.sar_part  [svid] = 0  # clear all states
        self.sar_sl    [svid] = sl.u
        self.sar_beacon[svid] = bitstring.BitStream()
        self.sar_param [svid] = bitstring.BitStream()
        return msg


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Galileo I/NAV message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    args = parser.parse_args()
    fp_disp = sys.stdout
    trace = libtrace.Trace(fp_disp, 0, args.color)
    galinav = GalInav(trace)
    try:
        raw = sys.stdin.buffer.read(30)
        while raw:
            payload = bitstring.ConstBitStream(raw)
            svid = payload.read(8).u
            inav = payload.read(LEN_INAV)
            payload.pos += 4  # spare
            msg = galinav.decode_inav(svid, inav)
            galinav.trace.show(0, msg)
            raw = sys.stdin.buffer.read(30)
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
