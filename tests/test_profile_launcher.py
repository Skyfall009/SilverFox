"""Safety contract for the native macOS profile launcher.

The actual launch and code-signing behavior must be checked on a Mac.
"""
import unittest
from pathlib import Path
from unittest.mock import patch
import build

ROOT = Path(__file__).resolve().parents[1]

class ProfileLauncherTests(unittest.TestCase):
    def test_entrypoint_is_native_launcher(self):
        source = (ROOT / 'build.py').read_text()
        self.assertIn('info["CFBundleExecutable"] = "SilverFoxLauncher"', source)
        self.assertIn('def compile_launcher(contents):', source)
        self.assertIn('contents / "MacOS" / "firefox"', source)

    def test_profile_is_explicit_and_separate(self):
        code = (ROOT / 'src/silverfox_launcher.c').read_text()
        self.assertIn('/Library/Application Support', code)
        self.assertIn('/Silver Fox', code)
        self.assertIn('/Profiles', code)
        self.assertIn('/Default', code)
        self.assertIn('"--no-remote"', code)
        self.assertIn('"--profile"', code)
        self.assertIn('execv(engine, args)', code)
        self.assertIn('lstat(path, &st)', code)
        self.assertIn('unsafe_gecko_argument', code)
        self.assertNotIn('Firefox/Profiles', code)
        self.assertIn('setenv("MOZ_APP_DATA", product, 1)', code)
        self.assertIn('setenv("MOZ_LOCAL_APP_DATA", cache_product, 1)', code)
        self.assertIn('"/Library/Caches"', code)
        self.assertIn('"/Silver Fox"', code)
        self.assertIn('ensure_private_dir(cache_product)', code)

    def test_compile_command_includes_native_source(self):
        with patch.object(build, 'run') as runner:
            build.compile_launcher(ROOT / 'Contents')
            command = runner.call_args.args
            self.assertEqual(command[:2], ('xcrun', 'clang'))
            self.assertIn('-Werror', command)
            self.assertEqual(command[-2], '-o')
            self.assertEqual(command[-1], ROOT / 'Contents/MacOS/SilverFoxLauncher')

if __name__ == '__main__':
    unittest.main()
