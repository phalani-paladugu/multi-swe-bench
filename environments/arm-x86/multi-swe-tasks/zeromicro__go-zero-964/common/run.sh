#!/bin/bash
set -euo pipefail
cd /home/go-zero
go test -v -count=1 ./...
