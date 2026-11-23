#!/bin/sh
# SPDX-License-Identifier: MPL-2.0
# Compatibility helper. The signed native app launcher is the single source
# of truth for profile isolation, even when launching from a terminal.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
LAUNCHER="$ROOT/build/Silver Fox.app/Contents/MacOS/SilverFoxLauncher"
if [ ! -x "$LAUNCHER" ]; then
    echo "Missing $LAUNCHER. Run python3 build.py first." >&2
    exit 1
fi
exec "$LAUNCHER" "$@"
