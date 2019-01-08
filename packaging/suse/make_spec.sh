#!/bin/bash

rm -r ./dist
./setup.py sdist
version=$(grep "version =" setup.py | sed "s|.*version = '\(.*\)',$|\1|g")
sed "s|^Version:\(.*\)__VERSION__.*$|Version:\1${version}|g" \
    ./packaging/suse/containerinfo-rpm.spec > ./dist/containerinfo-rpm.spec
echo $version
