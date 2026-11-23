"""Regression checks for Silver Fox's XML-based About dialog."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.build_classic import patch_about_xhtml


class AboutDialogTests(unittest.TestCase):
    def test_already_hidden_release_notes_does_not_duplicate_attribute(self):
        source = ('<?xml version="1.0"?>\n'
                  '<?xml-stylesheet href="chrome://global/skin/global.css" type="text/css"?>\n'
                  '<window xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">'
                  '<label hidden="true" id="releasenotes" is="text-link"/></window>')
        result = patch_about_xhtml(source)
        ET.fromstring(result)
        self.assertEqual(result.count('hidden="true"'), 1)
        self.assertIn('silverfox-about.css', result)
        self.assertEqual(patch_about_xhtml(result), result)

    def test_about_stylesheet_exists(self):
        css = (Path(__file__).resolve().parents[1] / 'src/about-dialog-overrides.css').read_text()
        self.assertIn('#0b0b0d', css)
        self.assertIn('button:hover', css)


if __name__ == '__main__':
    unittest.main()
