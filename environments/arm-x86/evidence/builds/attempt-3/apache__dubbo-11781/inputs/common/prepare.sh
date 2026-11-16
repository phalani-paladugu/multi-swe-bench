#!/bin/bash
set -euxo pipefail
cd /home/dubbo
./mvnw -B -pl dubbo-build-tools -DskipTests install
./mvnw -B -pl dubbo-common -Dsurefire.useFile=false -DfailIfNoTests=false -DskipTests test-compile
set +e
./mvnw -B -pl dubbo-common -Dsurefire.useFile=false -DfailIfNoTests=false test > /opt/task/preparation-tests.log 2>&1
status=$?
set -e
printf "%s\n" "$status" > /opt/task/preparation-tests.exit
git diff --exit-code
