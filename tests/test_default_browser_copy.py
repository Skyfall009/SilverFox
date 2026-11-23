import unittest
from src.build_classic import clean_default_browser_copy


class DefaultBrowserCopyTests(unittest.TestCase):
    def test_mac_default_browser_message_has_no_dash(self):
        source = "default-browser-prompt-message-pin-mac = Keep { -brand-short-name } at your fingertips — make it your default browser and keep it in your Dock."
        output = clean_default_browser_copy(source)
        self.assertIn("at your fingertips. Make it your default browser", output)
        self.assertNotIn("fingertips —", output)

    def test_mac_newtab_variant(self):
        source = "[macos] Keep { -brand-short-name } at your fingertips — make it your default and keep it in your Dock."
        self.assertIn("at your fingertips. Make it your default and", clean_default_browser_copy(source))

    def test_other_localization_unchanged(self):
        source = "some-other-message = Hello world — keep it simple."
        self.assertEqual(source, clean_default_browser_copy(source))


if __name__ == "__main__":
    unittest.main()
