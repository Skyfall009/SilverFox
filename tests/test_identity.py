"""Offline contract tests; runtime verification still requires macOS."""
import plistlib
import tempfile
import unittest
from pathlib import Path
from src.app_identity import patch_application_ini


class IdentityTests(unittest.TestCase):
    def test_patch_application_ini_keeps_upstream_options(self):
        with tempfile.TemporaryDirectory() as d:
            contents = Path(d)
            (contents / 'Resources').mkdir()
            ini = contents / 'Resources' / 'application.ini'
            ini.write_text('[App]\nVendor=Mozilla\nName=Firefox\nVersion=160.0.1\nRemotingName=firefox\n\n[Gecko]\nMinVersion=1\n')
            patch_application_ini(contents)
            result = ini.read_text()
            self.assertIn('Name=SilverFox', result)
            self.assertIn('Vendor=SilverFox', result)
            self.assertIn('RemotingName=silverfox', result)
            self.assertIn('Version=160.0.1', result)
            self.assertIn('[Gecko]\nMinVersion=1', result)
            patch_application_ini(contents)
            self.assertEqual(result, ini.read_text())

    def test_missing_ini_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):
                patch_application_ini(Path(d))

if __name__ == '__main__':
    unittest.main()
