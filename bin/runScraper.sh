#!/bin/bash

ME=`basename ${0}`
CURRENT_WORKSPACE=${1}
echo "I am ${ME} from ${CURRENT_WORKSPACE}"

CURRENT_PYTHONPATH=${CURRENT_WORKSPACE}

cd "${CURRENT_WORKSPACE}"
shift

PYTHONPATH="$CURRENT_PYTHONPATH" python3 scraper.py -db ${CURRENT_WORKSPACE}/movieDiversity.db -log DEBUG -loc Milano
PYTHONPATH="$CURRENT_PYTHONPATH" python3 scraper.py -db ${CURRENT_WORKSPACE}/movieDiversity.db -log DEBUG -loc "San Francisco"
PYTHONPATH="$CURRENT_PYTHONPATH" python3 scraper.py -db ${CURRENT_WORKSPACE}/movieDiversity.db -log DEBUG -loc "New York"
PYTHONPATH="$CURRENT_PYTHONPATH" python3 scraper.py -db ${CURRENT_WORKSPACE}/movieDiversity.db -log DEBUG -loc Cairo
PYTHONPATH="$CURRENT_PYTHONPATH" python3 scraper.py -db ${CURRENT_WORKSPACE}/movieDiversity.db -log DEBUG -loc München
