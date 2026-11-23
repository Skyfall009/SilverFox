import unittest
from src.mac_bundle_metadata import patch_browser_handler_names
from src.build_classic import patch_preferences_xhtml

class BrowserIdentityMetadataTests(unittest.TestCase):
    def test_handlers_have_independent_names(self):
        info = {"CFBundleURLTypes": [{"CFBundleURLName": "org.mozilla.firefox", "CFBundleURLSchemes": ["http", "https"]}], "CFBundleDocumentTypes": [{"CFBundleTypeName": "Firefox HTML Document"}]}
        patch_browser_handler_names(info)
        self.assertEqual(info["CFBundleURLTypes"][0]["CFBundleURLName"], "org.silverfox.browser.url-handler")
        self.assertEqual(info["CFBundleDocumentTypes"][0]["CFBundleTypeName"], "Silver Fox Browser Document")
        self.assertEqual(info["CFBundleURLTypes"][0]["CFBundleURLSchemes"], ["http", "https"])

    def test_preferences_stylesheet_is_idempotent(self):
        source = '<?xml version="1.0"?>\n<html xmlns="http://www.w3.org/1999/xhtml"></html>'
        changed = patch_preferences_xhtml(source)
        self.assertEqual(patch_preferences_xhtml(changed), changed)
        self.assertEqual(changed.count('silverfox-preferences.css'), 1)

if __name__ == '__main__':
    unittest.main()
