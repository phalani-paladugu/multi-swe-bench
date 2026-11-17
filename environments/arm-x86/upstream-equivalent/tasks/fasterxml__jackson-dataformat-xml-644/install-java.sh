#!/bin/bash
set -euxo pipefail
cat > /etc/apt/sources.list <<'SOURCES'
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250412T132500Z jammy main restricted universe multiverse
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250412T132500Z jammy-updates main restricted universe multiverse
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250412T132500Z jammy-security main restricted universe multiverse
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250412T132500Z jammy-backports main restricted universe multiverse
SOURCES
apt-get update
mapfile -t packages < /tmp/upstream-packages.txt
apt-get install -y --allow-downgrades "${packages[@]}"
