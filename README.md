# Silver Fox

A little bit of the browser I remember, built for the Mac I use today.

I've always liked the look of Firefox 2.0. The toolbar, the tabs, the familiar buttons and the overall simplicity of that era have stuck with me. Modern browsers are incredibly capable, but sometimes I miss an interface that felt a little more personal. That's the reason I started Silver Fox. I wanted to bring some of that familiar look back without giving up a modern browsing engine.

Silver Fox is an experimental, independent browser project for macOS. It uses an existing Mozilla Firefox engine with a classic inspired interface and its own name, icon and application identity. This isn't an attempt to replace Firefox. I still like Firefox. Silver Fox is simply another option for people who enjoy a more nostalgic style.

# Current state

Silver Fox is early alpha software. This is a personal project and it is still being tested. Some areas of the interface may retain upstream behavior or terminology, and some features may not work as expected. It is not a security audited browser and is not recommended for sensitive or everyday browsing.

The application is designed to coexist with Firefox and other browsers on the same Mac. Its macOS bundle identifier is org.silverfox.browser. A small native macOS launcher now enforces a dedicated profile path on every normal launch, instead of allowing Firefox to choose a profile from its shared registry. This needs to be verified on your Mac before other people use the release. Silver Fox should never be pointed at the same live profile as Firefox.

# How Silver Fox works

This repository contains the scripts, styles and artwork needed to create Silver Fox on macOS. The build process downloads a pinned Mozilla Firefox release, checks its SHA256 checksum, applies the Silver Fox interface and identity changes, and creates a local macOS application bundle. The browser engine is precompiled upstream software. This project does not compile the Firefox engine from source.

The familiar back, forward, reload and home controls use a neutral charcoal and gray look. The About window uses a dark theme, while the browser itself keeps a classic style. Silver Fox uses its own app icon and an independent application name where the build can change it safely.

DuckDuckGo is the initial homepage and default search provider. Users can change their homepage and search preferences. Mozilla account sign in and Sync are disabled, along with several optional feedback, telemetry and promotional integrations through local policies and preferences. These settings reduce some Firefox specific services but do not guarantee that the application makes no connections to Mozilla. Security related services, extensions and ordinary browsing may still make network requests. Those behaviors should be tested rather than assumed.

# Building on macOS

You need a Mac, Python 3.9 or newer, Apple command line developer tools (including xcrun and clang), an internet connection and space for the Firefox download and the finished application.

To install the developer tools if needed, use:

```sh
xcode-select --install
```

From the extracted project folder, run:

```sh
python3 build.py --no-open
open "build/Silver Fox.app"
```

The finished application will be inside the build folder. You can move it to Applications after closing it. The updated launcher changes startup behavior, so first launch it with an empty Silver Fox profile and verify the active Root Directory before importing any data. Since this is a locally signed experimental build, it is not equivalent to a notarized public release. You should not bypass system security protections to get it running.

If you have an older Silver Fox installation, close it before rebuilding and remove any obsolete copies from your Dock. macOS sometimes remembers an earlier browser registration. The builder now refreshes its Launch Services registration after building. For the most consistent behavior, keep one copy of Silver Fox at a stable location, such as Applications. Silver Fox currently hides the in-browser Make Default control because macOS has shown the upstream name, Firefox, in that system confirmation on some test systems. If you want to change your Mac default browser, use System Settings, Desktop & Dock, Default web browser and select Silver Fox after placing it in Applications. A system confirmation that still says Firefox means identity registration is not fully resolved; do not use that dialog as evidence of separation.

# Profiles and privacy

Silver Fox now uses a native startup launcher that sets an explicit profile directory at `~/Library/Application Support/Silver Fox/Profiles/Default`. The startup command also uses `--no-remote` and blocks external profile-selection arguments, so a normal launch must not silently fall back to a Firefox profile. You can check the expected directory with `"build/Silver Fox.app/Contents/MacOS/SilverFoxLauncher" --silverfox-profile-path`. In each browser, open `about:profiles` and compare the root directories of the profiles marked as in use; they must differ. The Firefox profile registry may still appear in upstream browser UI, so the active root directory is the key check. For details, see [ISOLATION.md](ISOLATION.md).

Automatic application updates are disabled because an unmodified Firefox update could overwrite Silver Fox's interface changes. That is a serious security limitation. The pinned engine must be reviewed and updated regularly, and this project should not be relied on as a secure primary browser while that maintenance process is incomplete. Turning off optional Mozilla telemetry is not the same thing as independently auditing every possible network connection.

Silver Fox has no independent cloud account or synchronization service. Do not enter Firefox account credentials expecting Silver Fox to provide its own account system. Browser profiles and browsing data should be backed up carefully before switching builds.

# Open source and legal information

Silver Fox is an independent project and is not created, maintained, sponsored, authorized or endorsed by Mozilla. Firefox and Mozilla are trademarks of their respective owners. The Firefox engine and related upstream components retain their original authorship, copyright notices, licenses and other legal obligations. The project's name and icon are not intended to represent an official Mozilla product.

The Mozilla Public License 2.0 is included as LICENSE. Original Silver Fox source changes carry license notices in their files. The upstream Firefox download is governed by the licenses and notices that accompany that release, including any applicable third party licenses. Building or distributing a modified browser does not transfer ownership of Mozilla software or trademarks. Anyone planning to distribute completed application bundles should separately review the relevant source availability, notices, license terms, branding rules and platform signing requirements.

The repository is primarily intended to share build scripts and patches, not a prebuilt Firefox installer. It does not include an upstream Firefox binary or the download cache. Any logo, screenshot or other asset published with the project should only be used when its owner has granted the necessary rights. The project maintainer is responsible for confirming the provenance and redistribution rights of the Silver Fox artwork.

These statements describe the project and its intended licensing approach; they are not a legal opinion or a guarantee of compliance. Mozilla's license terms are available at https://www.mozilla.org/en-US/MPL/2.0/ and its trademark guidelines at https://www.mozilla.org/en-US/foundation/trademarks/policy/.

# Feedback and contributions

I built Silver Fox because I missed the look of Firefox 2.0 and wanted to see what that design could feel like again. If you try it, I would genuinely appreciate feedback about the interface, usability and macOS compatibility.

Please report Silver Fox bugs in this project's GitHub Issues page when it is available, not in Mozilla's Firefox bug tracker. The build attempts to disable Firefox feedback commands, but this is still an alpha project and any remaining Mozilla reporting entry points should be reported here so they can be reviewed.

Contributions and suggestions are welcome. I especially appreciate help identifying unmodified upstream branding, improving profile isolation, testing on different Macs, documenting third party notices and keeping the browser engine current with security releases.

Thanks for taking a look at Silver Fox.

The optional macOS default browser message uses separate sentences instead of a long dash. This is a wording adjustment only; it does not change the known macOS default browser naming limitation.

# Updating an earlier alpha build

If you have previously used Silver Fox before this isolation update, do not assume its old browsing data was stored separately. Quit both browsers, back up your existing Firefox profile before launching the new build, and avoid deleting any existing Firefox profiles. This release will start Silver Fox with a clean, separate profile. To transfer data later, copy it into that profile only after verifying the two profile roots are different. This update makes no automatic changes to existing Firefox profile data.

The native launcher is new code and has not yet been tested on macOS in this environment. Please do not recommend this build to other users until Finder launch, code signing, and profile root isolation have been verified on a Mac.


Silver Fox's native launcher additionally sets `MOZ_APP_DATA` and
`MOZ_LOCAL_APP_DATA` to independent directories inside your Library folder.
This prevents `about:profiles` from using Firefox's existing profile
registry. See `ISOLATION.md` for verification steps. Existing Firefox data
is not moved or deleted.
