#!/bin/bash
set -euxo pipefail
cat > /etc/apt/sources.list <<'SOURCES'
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250331T074000Z focal main restricted universe multiverse
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250331T074000Z focal-updates main restricted universe multiverse
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250331T074000Z focal-security main restricted universe multiverse
deb [check-valid-until=no] https://snapshot.ubuntu.com/ubuntu/20250331T074000Z focal-backports main restricted universe multiverse
SOURCES
echo 'deb [signed-by=/usr/share/keyrings/azul.gpg] https://repos.azul.com/zulu/deb stable main' > /etc/apt/sources.list.d/zulu.list
apt-get update
mapfile -t packages < /tmp/upstream-packages.txt
apt-get install -y --allow-downgrades "${packages[@]}"
