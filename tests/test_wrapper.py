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

        self.assertEqual(output.getvalue(), b"yes\r")

    def test_responder_does_not_confirm_blocked_rm_command(self) -> None:
        output = io.BytesIO()
        responder = ConfirmationResponder(config=AyeConfig(), dry_run=False)
        prompt = "Claude wants to run: rm -rf ./dist\nType yes to continue"

        responder.maybe_confirm(output, prompt)

        self.assertEqual(output.getvalue(), b"")

    def test_responder_flags_blocked_rm_without_prompt(self) -> None:
        responder = ConfirmationResponder(config=AyeConfig(), dry_run=False)

        blocked = responder.maybe_blocked("Bash(rm -rf /tmp/test_claude_confirm_dir)\nRunning...")

        self.assertTrue(blocked)

    def test_responder_keeps_blocking_future_prompt_until_manual_input(self) -> None:
        output = io.BytesIO()
        responder = ConfirmationResponder(config=AyeConfig(), dry_run=False)
        responder.maybe_blocked("Bash(rm -rf /tmp/test_claude_confirm_dir)\nRunning...")

        responder.maybe_confirm(output, "Do you want to proceed?\n1. Yes\n2. No")

        self.assertEqual(output.getvalue(), b"")

        responder.clear_blocked()
        responder.maybe_confirm(output, "Do you want to proceed?\n1. Yes\n2. No")

        self.assertEqual(output.getvalue(), b"\r")

    def test_responder_clears_block_when_new_safe_shell_command_appears(self) -> None:
        output = io.BytesIO()
        responder = ConfirmationResponder(config=AyeConfig(), dry_run=False)
        responder.maybe_blocked("Bash(rm -rf /tmp/test_claude_confirm_dir)\nRunning...")
        responder.maybe_blocked("Bash(rm -rf /tmp/test_claude_confirm_dir)\nRunning...\nBash(git push origin main)\nRunning...")

        responder.maybe_confirm(output, "Do you want to proceed?\n1. Yes\n2. No")

        self.assertEqual(output.getvalue(), b"\r")

    def test_responder_clears_block_when_repeated_safe_command_reappears(self) -> None:
        output = io.BytesIO()
        responder = ConfirmationResponder(config=AyeConfig(), dry_run=False)
        responder.maybe_blocked("Bash(git push origin main)\nRunning...")
        responder.maybe_blocked("Bash(git push origin main)\nRunning...\nBash(rm -rf /tmp/test_claude_confirm_dir)\nRunning...")
        responder.maybe_blocked(
            "Bash(git push origin main)\nRunning...\n"
            "Bash(rm -rf /tmp/test_claude_confirm_dir)\nRunning...\n"
            "Bash(git push origin main)\nRunning..."
        )

        responder.maybe_confirm(output, "Do you want to proceed?\n1. Yes\n2. No")

        self.assertEqual(output.getvalue(), b"\r")

    def test_rolling_buffer_keeps_recent_lines(self) -> None:
        buffer = RollingTextBuffer(max_lines=2)

        buffer.append_bytes(b"one\ntwo\nthree")

        self.assertEqual(buffer.text, "one\ntwo\nthree")


if __name__ == "__main__":
    unittest.main()
