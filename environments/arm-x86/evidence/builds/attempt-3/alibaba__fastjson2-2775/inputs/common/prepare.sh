#!/bin/bash
set -euxo pipefail
cd /home/fastjson2
./mvnw -B -pl core -Dsurefire.useFile=false -DfailIfNoTests=false -DskipTests test-compile
set +e
./mvnw -B -pl core -Dsurefire.useFile=false -DfailIfNoTests=false test > /opt/task/preparation-tests.log 2>&1
status=$?
set -e
printf "%s\n" "$status" > /opt/task/preparation-tests.exit
git diff --exit-code
