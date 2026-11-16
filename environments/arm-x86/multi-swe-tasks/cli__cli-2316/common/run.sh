#!/bin/bash
set -euo pipefail
cd /home/cli
go test -vet=off -v -count=1 ./...
