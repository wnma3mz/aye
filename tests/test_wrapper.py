import io
import unittest

from aye.config import AyeConfig
from aye.cli import _wrapped_command
from aye.wrapper import ConfirmationResponder, RollingTextBuffer


class WrapperTests(unittest.TestCase):
    def test_wrapped_command_uses_direct_command(self) -> None:
        self.assertEqual(_wrapped_command(["claude", "--model", "sonnet"]), ["claude", "--model", "sonnet"])

    def test_wrapped_command_strips_separator(self) -> None:
        self.assertEqual(_wrapped_command(["--", "claude", "--model", "sonnet"]), ["claude", "--model", "sonnet"])

    def test_wrapped_command_defaults_to_claude(self) -> None:
        self.assertEqual(_wrapped_command([]), ["claude"])

    def test_responder_writes_yes_once_for_same_prompt(self) -> None:
        output = io.BytesIO()
        responder = ConfirmationResponder(config=AyeConfig(), dry_run=False)
        prompt = "Claude Code asks: type yes to continue"

        responder.maybe_confirm(output, prompt)
        responder.maybe_confirm(output, prompt)

        self.assertEqual(output.getvalue(), b"yes\n")

    def test_responder_does_not_confirm_blocked_rm_command(self) -> None:
        output = io.BytesIO()
        responder = ConfirmationResponder(config=AyeConfig(), dry_run=False)
        prompt = "Claude wants to run: rm -rf ./dist\nType yes to continue"

        responder.maybe_confirm(output, prompt)

        self.assertEqual(output.getvalue(), b"")

    def test_rolling_buffer_keeps_recent_lines(self) -> None:
        buffer = RollingTextBuffer(max_lines=2)

        buffer.append_bytes(b"one\ntwo\nthree")

        self.assertEqual(buffer.text, "one\ntwo\nthree")


if __name__ == "__main__":
    unittest.main()
