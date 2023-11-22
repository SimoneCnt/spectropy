#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import scipy.sparse
import chardet
import gzip

from . import spc

def read_spc(fname):
    f = spc.File(fname)
    x = f.x
    y = f.sub[0].y
    return x, y, None

def read_txt(fp):
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

def read_lrd11(fp):
    readpeaks = False
    readspectrum = False
    numdata = 0
    spectrum = list()
    peaksx = list()
    peaksy = list()
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
            peaksx.append(float(splt[0]))
            peaksy.append(float(splt[2]))
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
    return spectrum[0], spectrum[1], (np.array(peaksx), np.array(peaksy))


def read_rruff(fp, encoding=None):
    x, y = np.loadtxt(fp, delimiter=',', unpack=True)
    return x, y, None

def read_raman(fname):
    if fname.endswith('spc'):
        return read_spc(fname)
    if fname.endswith('gz'):
        with gzip.open(fname, mode='rb') as fp:
            encoding = chardet.detect(fp.read(2**10))['encoding']
        fp = gzip.open(fname, mode='rt', encoding=encoding)
    else:
        with open(fname, 'rb') as fp:
            encoding = chardet.detect(fp.read(2**10))['encoding']
        fp = open(fname, 'r', encoding=encoding)
    line = fp.readline()
    if line.split()[0] == "scanname":
        return read_txt(fp)
    elif line.split('=')[0] == "##NAMES":
        return read_rruff(fp)
    elif line.startswith('#! Defender LRD 1.1'):
        return read_lrd11(fp)
    else:
        return None, None, None


