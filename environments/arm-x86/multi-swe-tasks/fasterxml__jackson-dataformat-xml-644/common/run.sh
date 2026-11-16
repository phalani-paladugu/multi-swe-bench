#!/bin/bash
set -euo pipefail
cd /home/jackson-dataformat-xml
./mvnw -B -Dsurefire.useFile=false -DfailIfNoTests=false test
