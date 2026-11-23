# Silver Fox profile isolation

Silver Fox is a separate browser option, not a replacement for Firefox. Older alpha builds had a real bug: changing the app bundle name and `application.ini` was not enough to stop a normal launch from opening the standard Firefox profile registry.

The current build uses a native Mach-O executable, `SilverFoxLauncher`, as the macOS `CFBundleExecutable`. It launches the unrenamed bundled Firefox engine and ALWAYS passes `--no-remote --profile` with the following directory:

`~/Library/Application Support/Silver Fox/Profiles/Default`

The launcher creates these directories under the current user's home directory, refuses a symlink or a directory not owned by the current user, and exits if setup fails. It blocks arguments that could override the profile directory. Before starting the engine, it also sets `MOZ_APP_DATA` to
`~/Library/Application Support/Silver Fox` and `MOZ_LOCAL_APP_DATA` to
`~/Library/Caches/Silver Fox`. This makes Firefox's Toolkit Profile Service
read and write the Silver Fox `profiles.ini` and `installs.ini` instead of
Firefox's registry. It must keep these variables set for every startup,
including macOS Finder/Dock launches. The launcher overwrites inherited
values to prevent an external environment from selecting Firefox's registry.
The upstream engine and its internal library filenames remain unchanged.

## Verify before using the build

Quit Firefox and Silver Fox. Rebuild with `python3 build.py --no-open`. For a fresh build, launch `open "build/Silver Fox.app"`. Then open `about:support` in Silver Fox. Its Profile Folder must be
`~/Library/Application Support/Silver Fox/Profiles/Default`. Open
`about:profiles` and check that NO listed root/local directory points inside
`~/Library/Application Support/Firefox` or `~/Library/Caches/Firefox`.
The initial external profile may not appear in the registry list until it has
been registered using Silver Fox's profile manager; this is separate from
whether the active folder is correctly isolated.

After launching, you should see a Silver Fox profile registry at
`~/Library/Application Support/Silver Fox/profiles.ini` if the toolkit profile
service has written it. Do not copy Firefox's `profiles.ini` here; it may
contain paths to Firefox profiles and defeat the isolation you want.

To see what the launcher enforces, run:

```sh
"build/Silver Fox.app/Contents/MacOS/SilverFoxLauncher" --silverfox-profile-path
```

Check Firefox's active Root Directory separately. Quit and reopen both browsers, then ensure each retains its own history and extensions. Do not copy Firefox's `profiles.ini` into Silver Fox or point Silver Fox at an existing Firefox profile. Older alpha builds may have used a Firefox profile, so **back up that profile before upgrading**. The new launcher intentionally starts with a separate profile and does not silently migrate old user data.

## Known limitations

This project has not yet been built and launched on a Mac in the automated test environment. The native launcher needs macOS testing, including code signing, Finder/Dock launch, opening external links and startup with an existing Silver Fox process. Because `--no-remote` is used to prevent cross-browser remoting, opening a URL by starting another process while the profile is already in use may fail with a profile-in-use warning. The application data overrides separate the profile registry from Firefox, but this still requires testing on macOS and can change with future Firefox engine versions. Verify the active root, not the list of registered profile names alone.

Keep Firefox's original engine filenames and libraries. Renaming them is not necessary for profile isolation. Browser engine security updates and a complete independent service/network review remain outstanding release tasks.
