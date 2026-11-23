# SPDX-License-Identifier: MPL-2.0
"""Apply independent product branding while retaining upstream credit."""
import re
from base64 import b64encode
from shutil import copy2
from xml.sax.saxutils import escape

MOZILLA_BRANDING = "chrome/browser/content/branding/"
STARTUP_SPLASH_LOGO = "chrome/browser/content/activity-stream/data/content/assets/splash-logo.svg"
STARTUP_SPLASH_VIDEO = "chrome/browser/content/activity-stream/data/content/assets/splash-screen.webm"
TRADEMARK = "Firefox is a trademark of the Mozilla Foundation in the US and other countries."
ABOUT = "localization/en-US/browser/aboutDialog.ftl"


def _brand_fluent(source, name):
    source = re.sub(r"(?m)^(-brand-[\w-]+ = )(?:Mozilla )?Firefox$", lambda m: m[1] + name, source)
    return re.sub(r"(?m)^trademarkInfo = .*", "trademarkInfo = " + TRADEMARK, source)


def _brand_properties(source, name):
    return re.sub(r"(?m)^(brand\w+Name=)(?:Mozilla )?Firefox$", lambda m: m[1] + name, source)


def _about_fluent(source):
    source = re.sub(
        r"(?m)^community-2 = .*",
        'community-2 = { -brand-short-name } is an independent browser project built on the open-source Firefox codebase. It is not developed, sponsored, or endorsed by Mozilla.',
        source,
    )
    replacements = {
        "bottom-links-terms = Terms of Use": "bottom-links-terms = ",
        "bottom-links-privacy = Privacy Notice": "bottom-links-privacy = ",
        "releaseNotes-link = What’s new": "releaseNotes-link = ",
        "releaseNotes-link = What's new": "releaseNotes-link = ",
        "help-link = Help": "help-link = ",
        "help-link = Silver Fox Help": "help-link = ",
        "helpus = Want to help?": "helpus = ",
        "submit-feedback = Submit Feedback": "submit-feedback = ",
        "community-get-involved = Make a donation or get involved!": "community-get-involved = ",
        "Updates disabled by your organization": "Automatic browser updates are disabled",
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    return source


def _image_svg(png):
    data = b64encode(png).decode("ascii")
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">'
        f'<image width="256" height="256" href="data:image/png;base64,{data}"/></svg>'
    ).encode()


def _wordmark_svg(name):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 330 52">'
        '<text x="0" y="38" font-family="sans-serif" font-size="38" font-weight="600" '
        f'fill="context-fill">{escape(name)}</text></svg>'
    ).encode()


def chrome_branding(name, assets):
    icons = {size: (assets / f"icon{size}.png").read_bytes() for size in (16, 32, 48, 64, 128, 192, 256, 384)}
    images = {f"icon{size}.png": icons[size] for size in (16, 32, 48, 64, 128)}
    images.update({
        "about.png": icons[128],
        "about-logo.png": icons[192],
        "about-logo@2x.png": icons[384],
        "about-logo-private.png": icons[192],
        "about-logo-private@2x.png": icons[384],
        "about-logo.svg": _image_svg(icons[256]),
        "about-wordmark.svg": _wordmark_svg(name),
        "firefox-wordmark.svg": _wordmark_svg(name),
        "document.ico": (assets / "app.ico").read_bytes(),
    })
    text = {
        "localization/en-US/branding/brand.ftl": lambda source: _brand_fluent(source, name),
        "chrome/en-US/locale/branding/brand.properties": lambda source: _brand_properties(source, name),
        ABOUT: _about_fluent,
    }
    # Replace startup splash assets with blank placeholders so Silver Fox
    # does not show the Firefox-branded splash animation on startup.
    replacements = {MOZILLA_BRANDING + key: content for key, content in images.items()}
    replacements[STARTUP_SPLASH_LOGO] = (assets / "blank-splash.svg").read_bytes()
    replacements[STARTUP_SPLASH_VIDEO] = (assets / "blank-splash.webm").read_bytes()
    return text, replacements


def install_platform_icons(runtime, assets):
    icon_dir = runtime / "browser/chrome/icons/default"
    if icon_dir.is_dir():
        for icon in icon_dir.glob("default*.png"):
            size = icon.stem.removeprefix("default")
            replacement = assets / f"icon{size}.png"
            if replacement.is_file():
                copy2(replacement, icon)
    if (runtime / "firefox.icns").is_file():
        copy2(assets / "app.icns", runtime / "firefox.icns")
    if (runtime / "firefox.exe").is_file():
        copy2(assets / "app.ico", runtime / "app.ico")
