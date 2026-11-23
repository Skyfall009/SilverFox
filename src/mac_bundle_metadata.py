# SPDX-License-Identifier: MPL-2.0
"""Rename browser-facing registration metadata without renaming Gecko binaries."""


def patch_browser_handler_names(info):
    """Use a separate display identity for URL/document registrations.

    CFBundleTypeName and CFBundleURLName are not the executable name; they
    describe what macOS exposes as the application's document and URL handlers.
    Firefox embeds Mozilla-specific names in these records.
    """
    for entry in info.get("CFBundleURLTypes", []):
        if not isinstance(entry, dict):
            continue
        entry["CFBundleURLName"] = "org.silverfox.browser.url-handler"
    for entry in info.get("CFBundleDocumentTypes", []):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("CFBundleTypeName", ""))
        if "firefox" in name.lower() or "mozilla" in name.lower():
            entry["CFBundleTypeName"] = "Silver Fox Browser Document"
    return info
