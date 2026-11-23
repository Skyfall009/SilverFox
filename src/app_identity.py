# SPDX-License-Identifier: MPL-2.0
"""Customize Gecko's application identity without renaming engine binaries.

The bundle display name alone does not isolate Firefox's profile registry.
Gecko reads Name, Vendor and RemotingName from application.ini at startup.
"""
from pathlib import Path

PRODUCT_NAME = "SilverFox"
VENDOR_NAME = "SilverFox"
REMOTING_NAME = "silverfox"


def patch_application_ini(contents: Path) -> Path:
    """Change only [App] identity keys, preserving all other upstream settings."""
    ini = contents / "Resources" / "application.ini"
    if not ini.is_file():
        raise FileNotFoundError(f"Cannot isolate the Silver Fox profile: missing {ini}")
    source = ini.read_text(encoding="utf-8")
    lines = source.splitlines(keepends=True)
    section = None
    found = set()
    output = []
    changed = {"Name": PRODUCT_NAME, "Vendor": VENDOR_NAME, "RemotingName": REMOTING_NAME}
    insert_at = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if section == "App" and insert_at is None:
                insert_at = len(output)
            section = stripped[1:-1]
        if section == "App" and not stripped.startswith(("#", ";")) and "=" in stripped:
            k, _, _ = stripped.partition("=")
            k = k.strip()
            if k in changed:
                output.append(f"{k}={changed[k]}\n")
                found.add(k)
                continue
        output.append(line)
    if insert_at is None:
        if section != "App":
            raise ValueError(f"Missing [App] section in {ini}")
        insert_at = len(output)
    output[insert_at:insert_at] = [f"{key}={changed[key]}\n" for key in changed if key not in found]
    ini.write_text("".join(output), encoding="utf-8")
    return ini
