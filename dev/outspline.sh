#!/bin/sh

# This script is meant to be executed from the root directory of the project
#  as `./dev/outspline.sh [OPTIONS]`

export PYTHONPATH="$PYTHONPATH:$PWD/src:"

python2 "./src/scripts/outspline" "$@"
