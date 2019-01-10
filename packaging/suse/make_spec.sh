#!/bin/bash 

abort()     { log "FATAL: $*" ; exit 1 ; }
usage()     {
    cat <<USAGE
usage (from containermetadata-rpm root directory):
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

dashes="-------------------------------------------------------------------"
header="${dashes}%n%cd - %an <%ae>"
body="- Commit %h on %ad: %n%n%w(77,2,2)%B"
datef="%a %b %e %H:%M:%S %Z %Y"

pushd ${workdir} >/dev/null
    rm -rf ./dist
    ./setup.py sdist
    version=$(grep "version =" setup.py | sed "s|.*version = '\(.*\)',$|\1|g")
    sed "s|^Version:\(.*\)__VERSION__.*$|Version:\1${version}|g" \
        ./packaging/suse/containermetadata-rpm.spec > ./dist/containermetadata-rpm.spec
    git log --no-merges --format="${header}%n%n${body}" \
		--date="format-local:${datef}" > ./dist/containermetadata-rpm.changes
popd >/dev/null
