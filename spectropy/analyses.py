#!/usr/bin/env python3

import numpy as np
import scipy.signal
import scipy.sparse

from .read_raman import read_raman

def find_peaks(ax, x, y, pfilter, vshift):
    peaks, _ = scipy.signal.find_peaks(y)
    prominences = scipy.signal.peak_prominences(y, peaks)[0]
    ymax = np.amax(y)
    for p,pp in zip(peaks, prominences):
        if 100*pp/ymax>pfilter:
           ax.text(x[p], y[p]+0.03+vshift, "%.1f"%x[p], horizontalalignment='center', verticalalignment='center', fontweight='bold')

def baseline_als(y, lam, p, niter=10):
    # From https://stackoverflow.com/questions/29156532/python-baseline-correction-library
    L = len(y)
    D = scipy.sparse.diags([1,-2,1],[0,-1,-2], shape=(L,L-2))
    D = lam * D.dot(D.transpose())
    w = np.ones(L)
    W = scipy.sparse.spdiags(w, 0, L, L)
    for i in range(niter):
        W.setdiag(w)
        Z = W + D
        z = scipy.sparse.linalg.spsolve(Z, w*y)
        w = p * (y > z) + (1-p) * (y < z)
    return z

def plot(ax, x, y, peaks, label=None, xmin=200, xmax=3000, color=None, vshift=0.0, pfilter=5.0, spl=None):

    nx = [ xx for xx, yy in zip(x, y) if xx>xmin and xx<xmax ]
    ny = [ yy for xx, yy in zip(x, y) if xx>xmin and xx<xmax ]
    x = np.array(nx)
    y = np.array(ny)
    ymin = np.amin(y)
    ymax = np.amax(y) - ymin
    y -= ymin
    y /= ymax

    if peaks:
        px, py = peaks
        pnx = [ xx for xx, yy in zip(px, py) if xx>xmin and xx<xmax ]
        pny = [ yy for xx, yy in zip(px, py) if xx>xmin and xx<xmax ]
        px = np.array(pnx)
        py = np.array(pny)
        py -= ymin
        py /= ymax

    if spl:
        z = baseline_als(y, spl[0], spl[1], niter=10)
        if spl[2]=='keep':
            z += vshift
            ax.plot(x, z, color=color, alpha=0.3)
        elif spl[2]=='remove':
            y -= z
            ymin = np.amin(y)
            ymax = np.amax(y) - ymin
            y -= ymin
            y /= ymax
            if peaks:
                npy = list()
                for pxx, pyy, in zip(px, py):
                    diff = 999999
                    diffy = None
                    for xx, zz in zip(x, z):
                        if abs(pxx-xx)<diff:
                            diff = abs(pxx-xx)
                            diffy = zz
                    npy.append(pyy-diffy)
                py = np.array(npy)
                py -= ymin
                py /= ymax

    find_peaks(ax, x, y, pfilter, vshift)
    y += vshift
    ax.plot(x, y, label=label, color=color)

    if peaks:
        py += vshift
        for ppx, ppy in zip(px,py):
            ax.text(ppx, ppy-0.04, "%.1f"%ppx, horizontalalignment='center', verticalalignment='center', fontstyle='italic', fontsize='small')
        ax.plot(px, py, 'o', color=color)


def clean_raman(x, y, xmin=200, xmax=3000, spl=None):
    nx = [ xx for xx, yy in zip(x, y) if xx>xmin and xx<xmax ]
    ny = [ yy for xx, yy in zip(x, y) if xx>xmin and xx<xmax ]
    x = np.array(nx)
    y = np.array(ny)
    ymin = np.amin(y)
    ymax = np.amax(y) - ymin
    y -= ymin
    y /= ymax
    if spl and spl[2]=='remove':
        z = baseline_als(y, spl[0], spl[1], niter=10)
        y -= z
        ymin = np.amin(y)
        ymax = np.amax(y) - ymin
        y -= ymin
        y /= ymax
    return x, y

