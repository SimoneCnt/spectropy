#!/usr/bin/env python3

from setuptools import setup, find_packages

exec(open("spectropy/version.py").read())

setup(
    name = 'spectropy',
    version = version,
    description = 'Simple tool to view, compare and match Raman spectra of minerals.',
    long_description = 'Simple tool to view, compare and match Raman spectra of minerals.',
    url = 'https://github.com/SimoneCnt/spectropy',
    author = 'Simone Conti',
    author_email = 'simonecnt@gmail.com',
    license = 'GPLv3',
    packages = find_packages(),
    package_data = {'spectropy': ['reference_library/*/*.gz']},
    install_requires = ['numpy', 'matplotlib', 'scipy', 'chardet', 'pyyaml'],
    entry_points={
        'console_scripts': [
            'spectropy = spectropy.gui:run_spectropy_gui',
        ]
    },
)

