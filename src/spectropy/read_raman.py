#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import scipy.sparse
import chardet

from . import spc

def read_spc(fname):
    f = spc.File(fname)
    x = f.x
    y = f.sub[0].y
    return x, y, None

def read_txt(fname, encoding=None):
    fp = open(fname, 'r')
    line = fp.readline()
    if not line.split()[0] == "scanname":
        print("invalid file :(")
        return 0, 0, None
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

def read_lrd11(fname, encoding=None):
    fp = open(fname, 'r', encoding=encoding)
    line = fp.readline()
    if not line.startswith('#! Defender LRD 1.1'):
        return 0, 0, None
    readpeaks = False
    readspectrum = False
    numdata = 0
    spectrum = list()
    peaks = list()
    for line in fp:
        splt = line.split()
        if len(splt)==0: continue
        key = splt[0]
        if key=='datetime': continue
        if key=='name':
            name=splt[1]
            continue
        if key=='ahurainvno':
            invno=splt[1]
            continue
        if key=='peaks':
            if splt[1]=='begin':
                readpeaks = True
                continue
            if splt[1]=='end':
                readpeaks = False
                continue
        if readpeaks:
            peaks.append(float(splt[0]))
            continue
        if key=='spectrum':
            if splt[1]=='begin':
                readspectrum = True
                continue
            if splt[1]=='end':
                readspectrum = False
                continue
        if readspectrum:
            if len(splt)==1:
                numdata = int(splt[0])
                continue
            x, y = float(splt[0]), float(splt[1])
            spectrum.append([x,y])
    spectrum = np.array(spectrum).transpose()
    return spectrum[0], spectrum[1], (np.array(peaks), np.zeros(len(peaks)))


def read_rruff(fname, encoding=None):
    x, y = np.loadtxt(fname, delimiter=',', unpack=True)
    return x, y, None

def read_raman(fname):
    if fname.endswith('spc'):
        return read_spc(fname)
    else:
        with open(fname, 'rb') as fp:
            encoding = chardet.detect(fp.read(2**10))['encoding']
        with open(fname, 'r', encoding=encoding) as fp:
            line = fp.readline()
            if line.split()[0] == "scanname":
                return read_txt(fname, encoding=encoding)
            elif line.split('=')[0] == "##NAMES":
                return read_rruff(fname, encoding=encoding)
            elif line.startswith('#! Defender LRD 1.1'):
                return read_lrd11(fname, encoding=encoding)
            else:
                return None, None, None


