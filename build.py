#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Build a standalone macOS Silver Fox.app from a verified Mozilla release."""
import argparse
import hashlib
import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

from src.build_classic import PROJECT, patch_installation
from src.app_identity import patch_application_ini
from src.mac_bundle_metadata import patch_browser_handler_names

VERSION = "160.0.1"
RELEASE = f"https://archive.mozilla.org/pub/firefox/releases/{VERSION}"
PACKAGE = f"mac/en-US/Firefox {VERSION}.dmg"
BUILD = PROJECT / "build"
CACHE = PROJECT / "upstream"
APP_NAME = "Silver Fox.app"


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def verified_download():
    expected = dict(line.split(maxsplit=1)[::-1] for line in
                    (PROJECT / "src/SHA256SUMS").read_text().splitlines())[PACKAGE]
    CACHE.mkdir(parents=True, exist_ok=True)
    target = CACHE / f"firefox-{VERSION}-mac.dmg"

    def valid(path):
        if not path.is_file():
            return False
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest() == expected

    if not valid(target):
        temp = target.with_suffix(".download")
        temp.unlink(missing_ok=True)
        try:
            print("Downloading verified Firefox release from Mozilla...", flush=True)
            with urlopen(f"{RELEASE}/{quote(PACKAGE)}", timeout=120) as response, temp.open("wb") as out:
                shutil.copyfileobj(response, out)
            if not valid(temp):
                raise ValueError("Downloaded Firefox DMG failed the pinned SHA-256 check")
            temp.replace(target)
        finally:
            temp.unlink(missing_ok=True)
    return target


def copy_app(dmg, stage):
    mount = stage / "mount"
    mount.mkdir()
    app = stage / APP_NAME
    attached = False
    try:
        run("hdiutil", "attach", "-nobrowse", "-readonly", "-mountpoint", mount, dmg)
        attached = True
        run("ditto", mount / "Firefox.app", app)
    finally:
        if attached:
            run("hdiutil", "detach", mount)
    return app


def fix_localized_app_names(contents):
    """Set macOS localized application display names in every known locale.

    Firefox includes localized InfoPlist.strings which can override the parent
    Info.plist and otherwise make Launch Services display "Firefox".
    """
    import re

    resources = contents / "Resources"
    for locale in resources.glob("*.lproj"):
        path = locale / "InfoPlist.strings"
        if path.exists():
            original = path.read_bytes()
            if original.startswith(b"bplist00"):
                values = plistlib.loads(original)
                if not isinstance(values, dict):
                    raise ValueError(f"Unexpected localization structure: {path}")
                values["CFBundleName"] = "Silver Fox"
                values["CFBundleDisplayName"] = "Silver Fox"
                path.write_bytes(plistlib.dumps(values, fmt=plistlib.FMT_BINARY))
                continue
            encoding = "utf-16" if original[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8"
            try:
                source = original.decode(encoding)
            except UnicodeError as exc:
                raise ValueError(f"Cannot decode localized app name: {path}") from exc
        else:
            source, encoding = "", "utf-8"

        # OpenStep .strings keys may be bare or quoted. Replace existing keys
        # rather than appending a duplicate key with undefined precedence.
        for key in ("CFBundleName", "CFBundleDisplayName"):
            pattern = rf'(?m)^(\s*"?{key}"?\s*=\s*)"(?:[^"\\]|\\.)*"(\s*;)'
            replacement = lambda m: m.group(1) + '"Silver Fox"' + m.group(2)
            source, matches = re.subn(pattern, replacement, source)
            if matches == 0:
                source += f'\n"{key}" = "Silver Fox";\n'
            elif matches > 1:
                raise ValueError(f"Duplicate localized {key} in {path}")
        path.write_bytes(source.encode(encoding))


def register_app_with_launch_services(app):
    """Refresh the OS registration so default-browser prompts use this name.

    This is not a replacement for a fresh build or for installing the app under
    a stable path. macOS can retain stale registrations of old copies.
    """
    lsregister = Path("/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister")
    if lsregister.exists():
        try:
            subprocess.run([str(lsregister), "-f", str(app)], check=True)
        except subprocess.CalledProcessError:
            print("Warning: macOS did not refresh Launch Services registration.", file=sys.stderr)


def prepare_app(app):
    contents = app / "Contents"
    patch_application_ini(contents)
    plist_path = contents / "Info.plist"
    info = plistlib.loads(plist_path.read_bytes())
    info["CFBundleName"] = "Silver Fox"
    info["CFBundleDisplayName"] = "Silver Fox"
    info["CFBundleIdentifier"] = "org.silverfox.browser"
    info["CFBundleGetInfoString"] = "Silver Fox, an independent browser based on Firefox"
    info["LSHasLocalizedDisplayName"] = True
    patch_browser_handler_names(info)
    # Keep the original Mozilla entrypoint. macOS may terminate Firefox with
    # SIGKILL when the code-signed executable is launched as a helper instead
    # of the CFBundleExecutable recorded by Launch Services.
    info["CFBundleExecutable"] = "firefox"
    info.pop("CFBundleIconName", None)
    plist_path.write_bytes(plistlib.dumps(info, sort_keys=False))
    fix_localized_app_names(contents)

    # The official Firefox executable has Mozilla production entitlements
    # including restricted capabilities (e.g. passkey-related entitlements).
    # Retaining those with an ad-hoc signature causes AMFI to SIGKILL firefox:
    # "The file is adhoc signed but contains restricted entitlements".
    # Explicitly replace, rather than preserve, the executable entitlements.
    # This allowlist contains only ordinary hardened-runtime exceptions used by
    # Firefox; it intentionally omits Apple-private / provisioned capabilities.
    local_entitlements = {
        "com.apple.security.cs.allow-jit": True,
        "com.apple.security.cs.allow-unsigned-executable-memory": True,
        "com.apple.security.cs.disable-library-validation": True,
        "com.apple.security.cs.allow-dyld-environment-variables": True,
    }
    with tempfile.TemporaryDirectory(prefix="silverfox-sign-") as signing_dir:
        entitlements_path = Path(signing_dir) / "local-entitlements.plist"
        entitlements_path.write_bytes(plistlib.dumps(local_entitlements))
        # Signing the outer app also re-signs its main firefox executable.
        # Do not preserve production entitlements/flags, and do not use --deep
        # to re-sign the separately signed Mozilla helper applications.
        run("codesign", "--force", "--sign", "-",
            "--entitlements", entitlements_path, app)
    run("codesign", "--verify", "--deep", "--strict", "--verbose=2", app)



def main():
    if sys.platform != "darwin":
        sys.exit("This package builds a native .app on macOS. Run it on a Mac.")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-open", action="store_true", help="Do not open the app after building")
    args = parser.parse_args()
    BUILD.mkdir(exist_ok=True)
    destination = BUILD / APP_NAME
    with tempfile.TemporaryDirectory(prefix="silverfox-", dir=BUILD) as tmp:
        stage = Path(tmp)
        app = copy_app(verified_download(), stage)
        patch_installation(app / "Contents/Resources")
        prepare_app(app)
        backup = stage / "previous.app"
        if destination.exists():
            destination.replace(backup)
        try:
            app.replace(destination)
        except Exception:
            if backup.exists():
                backup.replace(destination)
            raise
    register_app_with_launch_services(destination)
    print(f"Built: {destination}")
    if not args.no_open:
        run("open", destination)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        sys.exit(f"Build failed: {exc}")
