#!/bin/bash
set -euxo pipefail
cd /home/cli
go mod download
go build ./...
git config --local user.useConfigOnly true
git diff --exit-code
