"""Checks for macOS localized display names. Does not replace on-device testing."""
import plistlib
import tempfile
import unittest
from pathlib import Path

from build import fix_localized_app_names


class MacDisplayNameTests(unittest.TestCase):
    def test_bare_and_quoted_keys_are_replaced_without_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            resources = Path(directory) / 'Resources'
            locale = resources / 'en.lproj'
            locale.mkdir(parents=True)
            source = locale / 'InfoPlist.strings'
            source.write_text('CFBundleName = "Firefox";\n"CFBundleDisplayName" = "Firefox";\n')
            fix_localized_app_names(Path(directory))
            result = source.read_text()
            self.assertNotIn('Firefox', result)
            self.assertEqual(result.count('Silver Fox'), 2)
            fix_localized_app_names(Path(directory))
            self.assertEqual(source.read_text(), result)

    def test_missing_display_name_is_added(self):
        with tempfile.TemporaryDirectory() as directory:
            resources = Path(directory) / 'Resources'
            locale = resources / 'fr.lproj'
            locale.mkdir(parents=True)
            source = locale / 'InfoPlist.strings'
            source.write_text('"CFBundleName" = "Firefox";\n')
            fix_localized_app_names(Path(directory))
            self.assertEqual(source.read_text().count('Silver Fox'), 2)

    def test_binary_plist_names(self):
        with tempfile.TemporaryDirectory() as directory:
            resources = Path(directory) / 'Resources'
            locale = resources / 'de.lproj'
            locale.mkdir(parents=True)
            source = locale / 'InfoPlist.strings'
            source.write_bytes(plistlib.dumps({'CFBundleName': 'Firefox'}, fmt=plistlib.FMT_BINARY))
            fix_localized_app_names(Path(directory))
            result = plistlib.loads(source.read_bytes())
            self.assertEqual(result['CFBundleName'], 'Silver Fox')
            self.assertEqual(result['CFBundleDisplayName'], 'Silver Fox')


if __name__ == '__main__':
    unittest.main()
