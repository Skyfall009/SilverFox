#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Patch the built-in browser chrome of the extracted Firefox 160.0.1 release."""
import re
from pathlib import Path
from shutil import copy2
from zipfile import ZIP_DEFLATED, ZipFile

from .branding import chrome_branding, install_platform_icons
from .omni import read_omni

PROJECT = Path(__file__).resolve().parent.parent
SRC = PROJECT / "src"
ASSETS = PROJECT / "assets"
CHROME = "chrome/browser/content/browser/"
XHTML = CHROME + "browser.xhtml"
CUSTOMIZATION = "moz-src/browser/components/customizableui/CustomizableUI.sys.mjs"
ABOUT_XHTML = CHROME + "aboutDialog.xhtml"
PREFERENCES_XHTML = "chrome/browser/content/preferences/preferences.xhtml"
ABOUT_CSS = CHROME + "aboutDialog.css"
BRAND_ASSETS = PROJECT / "branding"
PRODUCT_NAME = "Silver Fox"


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"Expected one occurrence of {old!r}")
    return source.replace(old, new, 1)


def patch_layout(source):
    source = replace_once(
        source,
        '<link rel="stylesheet" href="chrome://browser/skin/" />',
        '<link rel="stylesheet" href="chrome://browser/skin/" />\n'
        '  <link rel="stylesheet" href="chrome://browser/content/classic.css" />',
    )
    source = replace_once(source, 'autohide="true"\n           context="toolbar-context-menu"',
                          'context="toolbar-context-menu"')
    source = replace_once(
        source,
        'unifiedsearchbutton-available=""\n              sap-name="urlbar"',
        'sap-name="urlbar"',
    )
    start = source.index('  <toolbar id="TabsToolbar"')
    end = source.index('  <toolbar id="nav-bar"', start)
    tabs = source[start:end]
    source = source[:start] + source[end:]
    notifications = '  <toolbar id="notifications-toolbar"'
    source = replace_once(source, notifications, tabs + notifications)

    status = re.search(r'  <hbox id="statuspanel".*?</hbox>\n', source, re.S).group()
    source = replace_once(source, status, "")
    return replace_once(
        source,
        '  <html:div id="a11y-announcement"',
        '  <hbox id="classic-status-bar">\n' + status + '  </hbox>\n\n'
        '  <html:div id="a11y-announcement"',
    )


def patch_defaults(source):
    source = replace_once(source, '      lazy.sidebarRevampEnabled ? "sidebar-button" : null,\n', "")
    source = replace_once(
        source,
        '      Services.policies.isAllowed("removeHomeButtonByDefault")\n'
        '        ? null\n        : "home-button",\n      "spring",\n      "vertical-spacer",\n'
        '      "urlbar-container",\n      "spring",\n      "downloads-button",',
        '      "home-button",\n      "vertical-spacer",\n'
        '      "urlbar-container",\n      "search-container",\n      "downloads-button",\n'
        '      lazy.sidebarRevampEnabled ? "sidebar-button" : null,',
    )
    return replace_once(source, '      lazy.ippEnabled ? "ipprotection-button" : null,\n', "")


def patch_preferences(source):
    source = replace_once(
        source,
        'pref("browser.toolbars.bookmarks.visibility", "newtab");',
        'pref("browser.toolbars.bookmarks.visibility", "always");',
    )
    return source + "\n" + (SRC / "classic-prefs.js").read_text()

def patch_about_css(source):
    # Retained for compatibility with archive layouts that carry this CSS.
    return source + "\n" + (SRC / "about-dialog-overrides.css").read_text()


def patch_about_xhtml(source):
    """Load the override stylesheet without modifying existing XML attributes.

    Earlier builds inserted hidden="true" on labels that already had the
    attribute, creating invalid XML and breaking the entire About dialog.
    """
    stylesheet = ('<?xml-stylesheet href="chrome://browser/content/'
                  'silverfox-about.css" type="text/css"?>')
    if stylesheet in source:
        return source
    import re
    declarations = list(re.finditer(r'<\?xml-stylesheet\s+[^?]*\?>', source))
    if declarations:
        pos = declarations[-1].end()
        return source[:pos] + "\n" + stylesheet + source[pos:]
    declaration = re.match(r'<\?xml\s+[^?]*\?>', source)
    if declaration:
        pos = declaration.end()
        return source[:pos] + "\n" + stylesheet + source[pos:]
    return stylesheet + "\n" + source



def patch_preferences_xhtml(source):
    """Append a stylesheet PI to Settings UI, preserving valid XML."""
    stylesheet = ('<?xml-stylesheet href="chrome://browser/content/'
                  'silverfox-preferences.css" type="text/css"?>')
    if stylesheet in source:
        return source
    declarations = list(re.finditer(r'<\?xml-stylesheet\s+[^?]*\?>', source))
    if declarations:
        pos = declarations[-1].end()
        return source[:pos] + "\n" + stylesheet + source[pos:]
    declaration = re.match(r'<\?xml\s+[^?]*\?>', source)
    if declaration:
        pos = declaration.end()
        return source[:pos] + "\n" + stylesheet + source[pos:]
    return stylesheet + "\n" + source


def clean_default_browser_copy(source):
    """Use two plain sentences in the optional macOS default-browser prompt.

    These strings live in upstream Fluent localization assets rather than in
    Silver Fox's README. The user may have disabled the prompt, but it should
    remain correctly worded if surfaced by a later Firefox release.
    """
    return source.replace(
        "at your fingertips — make it your default browser",
        "at your fingertips. Make it your default browser",
    ).replace(
        "at your fingertips — make it your default and keep it in your Dock",
        "at your fingertips. Make it your default and keep it in your Dock",
    )


def patch_archive(output, patches, *, images=None):
    temporary = output.with_suffix(".tmp")
    with read_omni(output) as upstream, ZipFile(temporary, "w", ZIP_DEFLATED) as classic:
        for entry in upstream.infolist():
            data = upstream.read(entry)
            if images and entry.filename in images:
                data = images[entry.filename]
            elif patch := patches.get(entry.filename):
                data = patch(data.decode()).encode()
            # Prompt text is embedded in Firefox's localized Fluent files.
            # Apply only this targeted wording change; preserve other strings.
            if entry.filename.endswith(".ftl") and b"at your fingertips" in data:
                data = clean_default_browser_copy(data.decode("utf-8")).encode("utf-8")
            classic.writestr(entry, data)
        if images:
            classic.write(SRC / "classic.css", CHROME + "classic.css")
            classic.write(SRC / "about-dialog-overrides.css", CHROME + "silverfox-about.css")
            classic.write(SRC / "silverfox-preferences.css", CHROME + "silverfox-preferences.css")
    temporary.replace(output)


def patch_installation(runtime):
    text_branding, images = chrome_branding(PRODUCT_NAME, BRAND_ASSETS)
    browser = runtime / "browser"
    patch_archive(runtime / "omni.ja", {CUSTOMIZATION: patch_defaults})
    patch_archive(browser / "omni.ja", {
        XHTML: patch_layout,
        ABOUT_XHTML: patch_about_xhtml,
        PREFERENCES_XHTML: patch_preferences_xhtml,
        ABOUT_CSS: patch_about_css,
        **text_branding,
        "defaults/preferences/firefox.js": patch_preferences,
    }, images=images)
    install_platform_icons(runtime, BRAND_ASSETS)
    distribution = runtime / "distribution"
    distribution.mkdir(exist_ok=True)
    copy2(SRC / "policies.json", distribution / "policies.json")
