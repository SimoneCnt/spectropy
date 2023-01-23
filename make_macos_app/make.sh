#/bin/bash

source ../spectropy/version.py
sed "s/VERSION/$version/g" spectropy.platypus.template > spectropy.platypus

/usr/local/bin/platypus -P spectropy.platypus Spectropy.app

rm -f Spectropy.dmg
rm -rf tmpdir
mkdir -p tmpdir
ln -sf /Applications/ tmpdir/
cp -r Spectropy.app tmpdir/
hdiutil create -fs HFS+ -srcfolder tmpdir/ -volname Spectropy Spectropy.dmg
rm -rf tmpdir

