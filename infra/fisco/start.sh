#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f nodes/127.0.0.1/node0/config.ini ]; then
  echo 'Run bootstrap.sh first (downloads official FISCO BCOS v3.17.1).'
  exit 1
fi
bash nodes/127.0.0.1/start_all.sh
