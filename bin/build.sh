#!/bin/bash


ME=`basename ${0}`
CURRENT_WORKSPACE=${1}
echo "I am ${ME} from ${CURRENT_WORKSPACE}"

CURRENT_PYTHONPATH=${CURRENT_WORKSPACE}

cd "${CURRENT_WORKSPACE}"
shift

echo "Running ${ME} Using: ${CURRENT_WORKSPACE}"

PYTHONPATH="$CURRENT_PYTHONPATH" python3 tests/testSources.py $@ 
