#!/bin/bash 

abort()     { log "FATAL: $@" ; exit 1 ; }
usage()     {
    cat <<USAGE
usage (from containerinfo-rpm root directory):
    ./packaging/suse/make_spec.sh
USAGE
}

set -e

if [[ $PWD =~ .*packaging/suse$ ]]; then
    workdir=${PWD%%/packaging/suse}
elif [ -f "./setup.py" ]; then
    workdir="./"
else
    usage
    abort "setup.py script not found!"
fi

pushd ${workdir} >/dev/null
    rm -rf ./dist
    ./setup.py sdist
    version=$(grep "version =" setup.py | sed "s|.*version = '\(.*\)',$|\1|g")
    sed "s|^Version:\(.*\)__VERSION__.*$|Version:\1${version}|g" \
        ./packaging/suse/containerinfo-rpm.spec > ./dist/containerinfo-rpm.spec
popd >/dev/null
