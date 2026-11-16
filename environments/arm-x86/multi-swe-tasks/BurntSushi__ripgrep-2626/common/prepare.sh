#!/bin/bash
set -euxo pipefail
cd /home/ripgrep
cargo fetch --locked
cargo build --locked
cargo test --locked --no-run
git diff --exit-code
