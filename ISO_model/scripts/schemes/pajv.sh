#!/usr/bin/env bash
set -o pipefail
pajv $* 2>&1 | sed 's/,\s/\n/g' | sed 's/should NOT have additional properties/Has some wrong key/g' || exit 1