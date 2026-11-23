/* SPDX-License-Identifier: MPL-2.0 */
/*
 * Silver Fox native macOS entrypoint.
 *
 * Never allow Gecko's default Firefox profile lookup to run. Start the bundled
 * engine with a fixed, private, per-user profile directory or fail closed.
 * The upstream Firefox executable and its dependencies keep their filenames.
 */
#define _DARWIN_C_SOURCE 1
#include <errno.h>
#include <limits.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <mach-o/dyld.h>

static void error_exit(const char *message) {
    fprintf(stderr, "Silver Fox: %s: %s\n", message, strerror(errno));
    exit(1);
}

static void ensure_private_dir(const char *path) {
    struct stat st;
    if (lstat(path, &st) == 0) {
        if (!S_ISDIR(st.st_mode) || st.st_uid != getuid()) {
            fprintf(stderr, "Silver Fox: unsafe or non-owned profile directory: %s\n", path);
            exit(1);
        }
        return;
    }
    if (errno != ENOENT) error_exit(path);
    if (mkdir(path, 0700) != 0) error_exit(path);
}

static void concat(char *dest, size_t cap, const char *a, const char *b) {
    int n = snprintf(dest, cap, "%s%s", a, b);
    if (n < 0 || (size_t)n >= cap) {
        fprintf(stderr, "Silver Fox: path is too long\n");
        exit(1);
    }
}

static int unsafe_gecko_argument(const char *arg) {
    /* Do not allow CLI arguments to replace the isolated root or invoke the
       upstream profile picker. Treat case variations as equivalent. */
    static const char *blocked[] = {
        "-profile", "--profile", "-p", "--p", "-profilemanager",
        "--profilemanager", "-createprofile", "--createprofile",
        "-migration", "--migration", "-allow-downgrade", "--allow-downgrade",
        NULL
    };
    for (size_t i = 0; blocked[i]; ++i) {
        size_t len = strlen(blocked[i]);
        if (strncasecmp(arg, blocked[i], len) == 0 &&
            (arg[len] == '\0' || arg[len] == '=')) return 1;
    }
    return 0;
}

int main(int argc, char **argv) {
    struct passwd *pw = getpwuid(getuid());
    if (!pw || !pw->pw_dir || !pw->pw_dir[0]) {
        fprintf(stderr, "Silver Fox: cannot determine current user's home directory\n");
        return 1;
    }
    char support[PATH_MAX], product[PATH_MAX], profiles[PATH_MAX], profile[PATH_MAX];
    char cache_root[PATH_MAX], cache_product[PATH_MAX];
    concat(support, sizeof support, pw->pw_dir, "/Library/Application Support");
    concat(product, sizeof product, support, "/Silver Fox");
    concat(profiles, sizeof profiles, product, "/Profiles");
    concat(profile, sizeof profile, profiles, "/Default");
    concat(cache_root, sizeof cache_root, pw->pw_dir, "/Library/Caches");
    concat(cache_product, sizeof cache_product, cache_root, "/Silver Fox");
    ensure_private_dir(support);
    ensure_private_dir(product);
    ensure_private_dir(profiles);
    ensure_private_dir(profile);
    ensure_private_dir(cache_root);
    ensure_private_dir(cache_product);

    /* IMPORTANT: --profile isolates the active profile only. Firefox otherwise
       still loads the profile registry from ~/Library/Application Support/Firefox,
       which leaks Firefox profiles into Silver Fox's about:profiles page.
       These Gecko-supported overrides isolate profiles.ini, installs.ini,
       Profile Groups and local cache data as well. We overwrite inherited
       values so launching from a customized shell cannot redirect Silver Fox
       back into another application's registry. */
    if (setenv("MOZ_APP_DATA", product, 1) != 0) error_exit("setting Silver Fox application data root");
    if (setenv("MOZ_LOCAL_APP_DATA", cache_product, 1) != 0) error_exit("setting Silver Fox local data root");

    /* The --no-remote flag prevents an existing Firefox process from handling
       this launch. The --profile path prevents Firefox registry lookup. */
    char exe[PATH_MAX];
    uint32_t size = sizeof exe;
    if (_NSGetExecutablePath(exe, &size) != 0) {
        fprintf(stderr, "Silver Fox: executable path is too long\n");
        return 1;
    }
    char *slash = strrchr(exe, '/');
    if (!slash) {
        fprintf(stderr, "Silver Fox: executable has no directory\n");
        return 1;
    }
    slash[1] = '\0';
    char engine[PATH_MAX];
    concat(engine, sizeof engine, exe, "firefox");

    if (argc > 1 && strcmp(argv[1], "--silverfox-profile-path") == 0) {
        puts(profile);
        return 0;
    }
    for (int i = 1; i < argc; i++) {
        if (unsafe_gecko_argument(argv[i])) {
            fprintf(stderr, "Silver Fox: use of Firefox profile selection flags is blocked to protect existing profiles\n");
            return 2;
        }
    }
    char **args = calloc((size_t)argc + 5, sizeof(char *));
    if (!args) error_exit("allocating launch arguments");
    size_t out = 0;
    args[out++] = engine;
    args[out++] = "--no-remote";
    args[out++] = "--profile";
    args[out++] = profile;
    for (int i = 1; i < argc; i++) args[out++] = argv[i];
    args[out] = NULL;
    execv(engine, args);
    error_exit("starting bundled browser engine");
    return 1;
}
