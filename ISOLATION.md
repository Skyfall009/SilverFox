# Silver Fox and Firefox can coexist

Silver Fox is an independent **application identity** built on Firefox technology. It is not a replacement for Mozilla Firefox.

## Separate application, profile and data

The macOS bundle uses `CFBundleIdentifier=org.silverfox.browser`, with a Silver Fox name and icon. The builder changes `Contents/Resources/application.ini` from upstream Firefox identity settings to `Name=SilverFox`, `Vendor=SilverFox` and `RemotingName=silverfox` before code signing. Gecko uses those values for profile and remote-instance identity; the intent is that Finder/Dock launches create their own Silver Fox profile registry and data directories, without opening the Firefox profile or conflicting with its running process. This needs to be validated in the built macOS app before distribution.

**Check after first launch:** in *both* browsers, open `about:profiles` and `about:support`. Confirm their root and local profile directories are different, and that they are not sharing any `profiles.ini` or profile-group state. The exact path is controlled by Gecko; do not infer it only from the Finder app name. Test that both browsers can run at the same time. Firefox's normal profile root is `~/Library/Application Support/Firefox` on macOS. Silver Fox should use a separate location under Application Support.

Don't manually copy or link a Firefox profile into Silver Fox. Running two Gecko instances against one profile can corrupt data.

## Why `firefox`, `XUL` and `lib*.dylib` still appear

Those are names of the **Mozilla engine binaries and internal libraries**, not a sign that Silver Fox uses the installed Firefox app or its user data. Renaming these is dangerous: Gecko and dyld may expect specific locations and binary names. Silver Fox carries a separate copy of the engine inside its own `.app` bundle. The actual upstream libraries and executable retain their original filenames.

## Existing Silver Fox users

Switching application identity can create a **new, empty Silver Fox profile** on next launch. It does not delete an old Silver Fox profile. Back up the existing one before updating; do not migrate a normal Firefox profile automatically. If you had been using Silver Fox with a shared Firefox profile, quit both browsers and inspect the profile locations before resuming.

## Testing before GitHub releases

- Launch from Finder, Dock, and `open "build/Silver Fox.app"`.
- Launch Firefox at the same time; confirm different tabs, history, extensions and bookmarks.
- Inspect both `about:profiles` pages and actual Application Support directories.
- Verify About Silver Fox, main app/window title, Dock name, and macOS menu bar.
- Test opening external web links and registering either app as the default browser.
- Check for unwanted Mozilla services using browser/network logging. Changing the name and disabling Sync/telemetry is **not** a guarantee of zero Mozilla traffic.
- Update the underlying Firefox engine for security fixes before releasing a build to other users.

The source patch can be syntax-tested on other operating systems, but this exact `.app` launch and profile isolation require a Mac for validation.
