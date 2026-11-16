#!/bin/bash
set -euxo pipefail
cd /home/bat
cargo fetch --locked
cargo build --locked
cargo test --locked --no-run
git diff --exit-code
