#!/bin/bash
set -euo pipefail
cd /home/ripgrep
cargo test --locked
