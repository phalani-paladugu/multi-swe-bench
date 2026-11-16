#!/bin/bash
set -euo pipefail
cd /home/fastjson2
./mvnw -B -pl core -Dsurefire.useFile=false -DfailIfNoTests=false test
