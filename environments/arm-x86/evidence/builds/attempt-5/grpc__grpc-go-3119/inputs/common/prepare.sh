#!/bin/bash
set -euxo pipefail
cd /home/grpc-go
go mod download
go build ./...
git diff --exit-code
