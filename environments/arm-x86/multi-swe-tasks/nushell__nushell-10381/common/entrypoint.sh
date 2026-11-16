#!/bin/bash
set -e
# Docker network=none does not always map the container hostname.
if ! grep -qw "$(hostname)" /etc/hosts; then
  printf "127.0.0.1 %s\n" "$(hostname)" >> /etc/hosts
fi
exec "$@"
