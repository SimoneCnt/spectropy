#!/usr/bin/env python3

import os

def write_raman(fname, x, y, name='SpectroPy', fmt='rruff'):
    if fmt=='rruff': return write_rruff(fname, x, y, name)
    if fname.endswith('.lrd'): return write_lrd11(fname, x, y, name, True)
    print('Unknown file format asked for %s' % (fname))

def write_rruff(fname, x, y, name):
    with open(fname, 'w') as fp:
        fp.write('##NAMES=%s\n' % (name))
        for xx, yy in zip(x, y):
            fp.write('%.6f, %.6f\n' % (xx, yy))
        fp.write('##END=\n')

def write_lrd11(fname, X, Y, name, ahuracheck=True):
    N = len(X)
    if N!=len(Y):
        print('Error! x and y size does not match!')
        return False
    ahurainvno, ext = os.path.splitext(os.path.basename(fname))
    if ahuracheck:
        if ext!='.lrd':
            print('Warning! Extension should be .lrd')
        if len(ahurainvno)!=6:
            print('Warning! Filename should be 6 characters long!')
        if ahurainvno.upper()!=ahurainvno:
            print('Warning! Filename should be uppercase!')
    fp = open(fname, 'w', encoding='UTF-16')
    fp.write('#! Defender LRD 1.1\n')
    fp.write('datetime 20030909 04:38:50\n')
    fp.write('name %s\n' % (name))
    fp.write('source \n')
    fp.write('ahurainvno %s\n' % (ahurainvno))
    fp.write('category User Added\n')
    fp.write('cas \n')
    fp.write('cluster 0\n')
    fp.write('peaks begin\n')
    fp.write('peaks end\n')
    fp.write('\n')
    fp.write('state\n')
    fp.write('preparation\n')
    fp.write('waveunits delta cm-1\n')
    fp.write('wavenumrange 250 2844\n')
    fp.write('SNR 96.656761 118.208557 104.286301\n')
    fp.write('group \n')
    fp.write('librarytype 1\n')
    fp.write('spectrum begin\n')
    fp.write('%d\n' % (N))
    for x, y in zip(X, Y):
        fp.write('%.6f %.6f\n' % (x, y))
    fp.write('spectrum end\n')
    fp.close()
    return True


