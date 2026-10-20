#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -f build_chain.sh ]; then
  curl -fL --retry 2 https://raw.githubusercontent.com/FISCO-BCOS/FISCO-BCOS/v3.17.1/tools/BcosAirBuilder/build_chain.sh -o build_chain.sh
fi
if [ ! -f nodes/127.0.0.1/node0/config.ini ]; then
  bash build_chain.sh -l 127.0.0.1:4 -o nodes -v v3.17.1
fi
python3 configure.py
bash start.sh
