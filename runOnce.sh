#/bin/bash

WORKING_DIR=`pwd`

${WORKING_DIR}/bin/runScraper.sh ${WORKING_DIR} >> ${WORKING_DIR}/latestRun.log 2>&1
