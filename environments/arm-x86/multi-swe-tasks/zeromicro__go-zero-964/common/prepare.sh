#!/bin/bash
set -euxo pipefail
cd /home/go-zero
go mod download
go build ./...
git diff --exit-code
