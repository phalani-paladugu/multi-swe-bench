#!/bin/bash
set -euo pipefail
cd /home/nushell
cargo test --locked
