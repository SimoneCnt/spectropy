#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import scipy.sparse

from . import spc

def read_spc(fname):
    f = spc.File(fname)
    x = f.x
    y = f.sub[0].y
    return x, y, None

def read_txt(fname):
    fp = open(fname, 'r')
    line = fp.readline()
    if not line.split()[0] == "scanname":
        print("invalid file :(")
        return
    spectrumn = 0
    spectrumx = list()
    spectrumy = list()
    peaksn = 0
    peaksx = list()
    peaksy = list()
    for line in fp.readlines():
        splt = line.split()
        if splt[0]=="spectrum":
            spectrumn = int(splt[1])
            continue
        if splt[0]=="peaks":
            peaksn = int(splt[1])
            continue
        if spectrumn>0:
            spectrumx.append(float(splt[0]))
            spectrumy.append(float(splt[1]))
            spectrumn -= 1
        if peaksn>0:
            peaksx.append(float(splt[0]))
            peaksy.append(float(splt[1]))
            peaksn -= 1
    return np.array(spectrumx), np.array(spectrumy), (np.array(peaksx), np.array(peaksy))

def read_rruff(fname):
    x, y = np.loadtxt(fname, delimiter=',', unpack=True)
    return x, y, None

def read_raman(fname):
    if fname.endswith('spc'):
        return read_spc(fname)
    else:
        with open(fname, 'r') as fp:
            line = fp.readline()
            if line.split()[0] == "scanname":
                return read_txt(fname)
            elif line.split('=')[0] == "##NAMES":
                return read_rruff(fname)
            else:
                return None, None, None


