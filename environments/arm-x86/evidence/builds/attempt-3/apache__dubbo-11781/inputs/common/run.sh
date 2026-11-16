#!/bin/bash
set -euo pipefail
cd /home/dubbo
./mvnw -B -pl dubbo-common -Dsurefire.useFile=false -DfailIfNoTests=false test
