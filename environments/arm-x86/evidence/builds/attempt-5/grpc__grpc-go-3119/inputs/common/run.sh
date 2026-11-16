#!/bin/bash
set -euo pipefail
cd /home/grpc-go
go test -v -count=1 ./...
