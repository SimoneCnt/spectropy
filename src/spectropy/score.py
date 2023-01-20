#!/usr/bin/env python3

"""
https://dykuang.github.io/posts/2018/06/Matching-algorithm-for-Raman-Spectra/
https://github.com/dykuang/Raman-Spectral-Matching
"""

import os, platform
import numpy as np
import scipy
import pickle
import spectropy as spp

def get_user_data_dir():
    if platform.platform() in ['Linux', 'Darwin']:
        d = os.path.join(os.environ['HOME'], '.spectropy')
    elif platform.platform in ['Windows']:
        d = os.path.join(os.environ['APPDATA'], 'spectropy')
    else:
        d = os.path.join(os.environ['HOME'], '.spectropy')
    os.makedirs(d, exist_ok=True)
    return d

def load_reference_database(max_similar=2, preferred_laser=780, overwrite=False):
    reflib = os.path.join(get_user_data_dir(), 'reflib.pkl')
    if os.path.isfile(reflib):
        if overwrite:
            print('Reference library file already exists; removing it...')
            os.remove(reflib)
        else:
            print('Reference library file already exists; loading it...')
            with open(reflib, 'rb') as fp:
                data = pickle.load(fp)
            return data
    print('Creating reference library file...')
    refdirs_path = os.path.join(os.path.dirname(__file__), 'reference_library')
    refdirs = [ ['excellent_unoriented', 3],
                ['fair_unoriented', 2],
                ['poor_unoriented', 1], 
                ['unrated_unoriented', 0]
            ]
    alldata = dict()
    for refdir, quality in refdirs:
        for f in os.listdir(os.path.join(refdirs_path, refdir)):
            mineral, rruffid, _, laser, _, _, _, _ = os.path.basename(f).split('__')
            if mineral not in alldata.keys():
                alldata[mineral] = list() 
            laser = float(laser.split('_')[0]) if len(laser)>0 else 0.0
            alldata[mineral].append([f, rruffid, laser, quality, refdir])
    loaded = 0
    data = dict()
    for mineral, mindata in alldata.items():
        sdata = sorted(mindata, key=lambda d: (d[3], -abs(preferred_laser-d[2]), d[1]), reverse=True)
        pdata = sdata[0:max_similar]
        for f, rruffid, laser, quality, refdir in pdata:
            name = '%s__%g__%s' % (mineral, laser, rruffid)
            if name in data.keys(): continue
            x, y, _ = spp.read_raman(os.path.join(refdirs_path, refdir, f))
            data[name] = np.array([x,y])
            loaded += 1
            if loaded%100==0:
                print(loaded)
    print('Loaded %s spectra for %d different minerals!' % (loaded, len(alldata.keys())))
    print('Writing reference library to %s...' % (reflib))
    with open(reflib, 'wb') as fp:
        pickle.dump(data, fp)
    return data


def resample(x, y, xmin=250, xmax=1400, resolution=1.0):
    xmin = np.round(max(xmin, np.amin(x)))
    xmax = np.round(min(xmax, np.amax(x)))
    nump = int(np.round((xmax-xmin)/resolution)+1)
    xnew = np.linspace(xmin, xmax, nump)
    ynew = scipy.interpolate.splev(xnew, scipy.interpolate.splrep(x, y))
    ynew /= np.amax(ynew)
    return xnew, ynew

def print_candidates(match_score, name_in_lib):
    candidates_order = np.argsort(match_score)[::-1]
    matches = list()
    for i, c in enumerate(candidates_order[:10]):
        print("The top %d selection are %s with score: %.4f" % (i+1, name_in_lib[c], match_score[c]))
        matches.append(name_in_lib[c])
    return matches

def score(test, lib, resolution=0.5):
    xt, yt = test[0,:], test[1,:]
    xl, yl = lib[0,:], lib[1,:]
    xmin = max(np.amin(xt), np.amin(xl))
    xmax = min(np.amax(xt), np.amax(xl))
    xt, yt = resample(xt, yt, xmin, xmax, resolution)
    xl, yl = resample(xl, yl, xmin, xmax, resolution)
    # Pearson correlation coefficient [-1,1]
    rp = scipy.stats.pearsonr(yt, yl)[0]
    # Dot product between normalized vectors, or euclidean cosine [-1,1]
    dot = np.dot(yt,yl)/np.linalg.norm(yt)/np.linalg.norm(yl)
    # Squared Euclidean Cosine [0,1]
    sec = dot**2 
    # First-Difference Euclidean Cosine (SFEC) [0,1]
    ytd = np.diff(yt)
    yld = np.diff(yl)
    dotd = np.dot(ytd,yld)/np.linalg.norm(ytd)/np.linalg.norm(yld)
    sfec = dotd**2 
    return rp, dot, sfec

def score_all(x, y, lib_data):
    test = np.array([x,y])
    name_in_lib = list(lib_data.keys())
    n_lib = len(name_in_lib)
    match_score_rp = np.zeros(n_lib)
    match_score_dot = np.zeros(n_lib)
    match_score_sfec = np.zeros(n_lib)
    for i, name in enumerate(name_in_lib):
        try:
            rp, dot, sfec = score(test, lib_data[name])
        except:
            rp = dot = sfec = 0.0
            print('Bugged!', name, '--disregard..')
        match_score_rp[i] = rp
        match_score_dot[i] = dot
        match_score_sfec[i] = sfec
    print('SFEC')
    m1 = print_candidates(match_score_sfec, name_in_lib)
    print('DOT')
    m2 = print_candidates(match_score_dot, name_in_lib)
    print('Pearson')
    m3 = print_candidates(match_score_rp, name_in_lib)
    return m1 + m2 + m3
