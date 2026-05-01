import contextlib
import io
import unittest
from unittest.mock import patch

from aye import __version__
from aye.cli import main


class CliTests(unittest.TestCase):
    def test_version_flag_prints_version(self) -> None:
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            exit_code = main(["--version"])

        self.assertEqual(exit_code, 0)
        self.assertEqual(output.getvalue().strip(), f"aye {__version__}")

    def test_update_command_calls_updater(self) -> None:
        with patch("aye.cli.update_current_binary", return_value=0) as update:
            exit_code = main(["update"])

        self.assertEqual(exit_code, 0)
        update.assert_called_once()


if __name__ == "__main__":
    unittest.main()
