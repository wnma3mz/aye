import unittest

from aye.detectors import find_blocked_command, find_confirmation, last_lines


class DetectorTests(unittest.TestCase):
    def test_detects_explicit_yes_prompt(self) -> None:
        text = "Preparing command\nType 'yes' to continue:"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.answer, "yes")
        self.assertEqual(match.rule_name, "explicit-type-yes")

    def test_only_scans_recent_lines(self) -> None:
        old_prompt = "Type yes to continue"
        recent_noise = "\n".join(f"line {index}" for index in range(20))

        match = find_confirmation(f"{old_prompt}\n{recent_noise}", scan_lines=5)

        self.assertIsNone(match)

    def test_last_lines_zero_returns_all_text(self) -> None:
        self.assertEqual(last_lines("a\nb\nc", 0), "a\nb\nc")

    def test_detects_yes_menu_choice_as_enter(self) -> None:
        text = "Do you want to proceed?\n1. Yes\n2. No"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_tool_permission_yn_prompt(self) -> None:
        text = "Allow this command to run? [y/N]"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-permission-yn")
        self.assertEqual(match.answer, "y")

    def test_does_not_confirm_bare_yn_prompt(self) -> None:
        match = find_confirmation("Continue? [y/N]")

        self.assertIsNone(match)

    def test_does_not_confirm_bare_yes_no_prompt(self) -> None:
        match = find_confirmation("Continue? yes/no")

        self.assertIsNone(match)

    def test_detects_blocked_rm_command(self) -> None:
        match = find_blocked_command("About to run: sudo rm -rf ./build\nType yes to continue")

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "rm")

    def test_blocked_rm_rule_does_not_match_normal_words(self) -> None:
        match = find_blocked_command("Please confirm the action\nType yes to continue")

        self.assertIsNone(match)


if __name__ == "__main__":
    unittest.main()
