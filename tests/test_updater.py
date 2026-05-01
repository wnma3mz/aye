import unittest
from unittest.mock import patch

from aye.updater import _asset_name, _platform_slug


class UpdaterTests(unittest.TestCase):
    def test_asset_name_includes_version_and_platform(self) -> None:
        with patch("platform.system", return_value="Darwin"), patch("platform.machine", return_value="arm64"):
            self.assertEqual(_asset_name("v0.0.2"), "aye-v0.0.2-darwin-arm64.tar.gz")

    def test_linux_x64_platform_slug(self) -> None:
        with patch("platform.system", return_value="Linux"), patch("platform.machine", return_value="x86_64"):
            self.assertEqual(_platform_slug(), "linux-x64")


if __name__ == "__main__":
    unittest.main()
