#!/bin/sh
# Launch Silver Fox with a separate profile without modifying the signed app.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
APP="$ROOT/build/Silver Fox.app"
PROFILE="$HOME/Library/Application Support/Silver Fox/Profile"
if [ ! -f "$APP/Contents/Info.plist" ]; then
    echo "Missing $APP. Run python3 build.py first." >&2
    exit 1
fi
mkdir -p "$PROFILE"
exec "$APP/Contents/MacOS/firefox" --no-remote --profile "$PROFILE" "$@"
