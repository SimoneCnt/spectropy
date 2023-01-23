#!/bin/bash

d=220605

unzip -u -d excellent_unoriented/ excellent_unoriented_${d}.zip
unzip -u -d fair_unoriented/ fair_unoriented_${d}.zip
unzip -u -d poor_unoriented/ poor_unoriented_${d}.zip
unzip -u -d unrated_unoriented/ unrated_unoriented_${d}.zip

gzip excellent_unoriented/*.txt
gzip fair_unoriented/*.txt
gzip poor_unoriented/*.txt
gzip unrated_unoriented/*.txt

