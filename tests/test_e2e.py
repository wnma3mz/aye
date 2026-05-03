import subprocess
import sys
import textwrap
import unittest


class EndToEndTests(unittest.TestCase):
    def test_cli_confirms_claude_style_menu_with_enter(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            print("Bash command", flush=True)
            print("Do you want to proceed?", flush=True)
            print("❯ 1. Yes", flush=True)
            print("  2. Yes, allow reading from tmp/ from this project", flush=True)
            print("  3. No", flush=True)
            print("Esc to cancel · Enter to select", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='\\r'", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_confirms_claude_trust_folder_with_enter(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            print(" > 1. Yes, I trust this folder", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='\\r'", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_confirms_codex_enter_menu_with_enter(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                print("1. Yes, proceed (y)", flush=True)
                print("2. Yes, and don't ask again for these files (a)", flush=True)
                print("3. No, and tell Codex what to do differently (esc)", flush=True)
                print("Press enter to confirm or esc to cancel", flush=True)
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='\\r'", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_confirms_gemini_allow_once_menu_with_enter(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            print("Confirm tool execution", flush=True)
            print("│ ● 1. Allow once", flush=True)
            print("│ ○ 2. Deny", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='\\r'", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_confirms_plain_yes_no_choice_lines_with_enter(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            print("Do you want to proceed?", flush=True)
            print("Yes, proceed", flush=True)
            print("No, cancel", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='\\r'", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_confirms_codex_style_yn_permission_with_y(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            print("Codex wants to run a shell command", flush=True)
            print("Allow this command to run? [y/N]", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                chars = sys.stdin.read(2)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={chars!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='y\\r'", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_confirms_gemini_style_yn_permission_with_y(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            print("Gemini wants to execute a command", flush=True)
            print("Approve command execution? (y/N)", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                chars = sys.stdin.read(2)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={chars!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='y\\r'", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_does_not_confirm_bare_yes_no_list(self) -> None:
        code = textwrap.dedent(
            r"""
            import select
            import sys
            import termios
            import tty

            print("Options:", flush=True)
            print("1. Yes", flush=True)
            print("2. No", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                char = sys.stdin.read(1) if ready else None
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received=None", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_does_not_confirm_after_dangerous_command_appears(self) -> None:
        code = textwrap.dedent(
            r"""
            import select
            import sys
            import termios
            import tty

            print("Bash(rm -rf /tmp/test_claude_confirm_dir)", flush=True)
            print("Running...", flush=True)
            for index in range(30):
                print(f"noise {index}", flush=True)
            print("Do you want to proceed?", flush=True)
            print("1. Yes", flush=True)
            print("2. No", flush=True)
            print("Enter to select", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                ready, _, _ = select.select([sys.stdin], [], [], 0.5)
                char = sys.stdin.read(1) if ready else None
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received=None", result.stdout)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_confirms_new_safe_command_after_old_dangerous_command(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                print("Bash(rm -rf /tmp/test_demo_dir)", flush=True)
                print("Waiting...", flush=True)
                print("Bash(git push origin main)", flush=True)
                print("Running...", flush=True)
                print("Bash command", flush=True)
                print("git push origin main", flush=True)
                print("Do you want to proceed?", flush=True)
                print("❯ 1. Yes", flush=True)
                print("  2. Yes, and don’t ask again for: git push:*", flush=True)
                print("  3. No", flush=True)
                print("Esc to cancel · Enter to select", flush=True)
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='\\r'", result.stdout)
        self.assertNotIn("Blocked auto-confirm", result.stderr)
        self.assertNotIn("Auto-confirming", result.stderr)

    def test_cli_verbose_prints_diagnostic_logs(self) -> None:
        code = textwrap.dedent(
            r"""
            import sys
            import termios
            import tty

            print("Do you want to proceed?", flush=True)
            print("1. Yes", flush=True)
            print("2. No", flush=True)
            print("Enter to select", flush=True)

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                char = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
            print()
            print(f"received={char!r}", flush=True)
            """
        )

        result = _run_aye_command(code, verbose=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("received='\\r'", result.stdout)
        self.assertIn("Auto-confirming: rule=ai-cli-yes-choice", result.stderr)


def _run_aye_command(code: str, *, verbose: bool = False) -> subprocess.CompletedProcess[str]:
    aye_args = ["-m", "aye.cli"]
    if verbose:
        aye_args.append("--verbose")
    return subprocess.run(
        [sys.executable, *aye_args, sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


if __name__ == "__main__":
    unittest.main()
