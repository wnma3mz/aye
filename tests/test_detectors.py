import unittest

from aye.detectors import find_blocked_command, find_confirmation, last_lines, latest_shell_command


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

    def test_detects_claude_three_choice_permission_menu(self) -> None:
        text = "\x1b[36mDo you want to proceed?\x1b[0m\n❯ 1. Yes\n  2. Yes, allow reading from tmp/ from this project\n  3. No"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_claude_menu_with_choice_descriptions(self) -> None:
        text = (
            "确认操作\n"
            "是否继续执行该操作?\n"
            "\n"
            "1. Yes\n"
            "   确认继续执行\n"
            "2. No\n"
            "   取消操作\n"
            "3. Type Something.\n"
            "\n"
            "4. Chat about this\n"
            "Enter to select"
        )

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_claude_trust_folder_prompt(self) -> None:
        text = " > 1. Yes, I trust this folder"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "claude-trust-folder")
        self.assertEqual(match.answer, "")

    def test_detects_claude_dark_mode_choice(self) -> None:
        text = "❯ 1. Dark mode ✔"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "claude-theme-choice")
        self.assertEqual(match.answer, "")

    def test_detects_selected_first_yes_choice_before_full_menu_arrives(self) -> None:
        text = "❯ 1. Yes"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "selected-first-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_press_enter_to_continue_prompt(self) -> None:
        text = "Press Enter to continue"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "press-enter-continue")
        self.assertEqual(match.answer, "")

    def test_detects_carriage_return_menu_output(self) -> None:
        text = "Do you want to proceed?\r\n> 1) Yes\r\n   Continue\r\n  2) No\r\n   Cancel"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")

    def test_detects_bracket_numbered_menu(self) -> None:
        text = "Confirm operation\n[1] Yes\n[2] No\nEnter to select"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")

    def test_detects_lettered_menu(self) -> None:
        text = "Confirm operation\nA. Yes, proceed\nB. No, cancel"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")

    def test_detects_bulleted_menu(self) -> None:
        text = "Press enter to confirm\n- Yes, proceed\n- No, cancel"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")

    def test_detects_gemini_yes_allow_once_menu(self) -> None:
        text = "Confirm tool execution\n│ ● 1. Yes, allow once\n│ ○ 2. No, cancel"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_gemini_allow_once_menu(self) -> None:
        text = "Confirm tool execution\n│ ● 1. Allow once\n│ ○ 2. Deny"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_plain_yes_no_choice_lines_with_context(self) -> None:
        text = "Do you want to proceed?\nYes, proceed\nNo, cancel"

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")

    def test_detects_codex_menu_after_long_multiline_command(self) -> None:
        text = """Would you like to run the following command?

Reason: Do you want me to retry the live stock data fetch outside the sandbox with the broken local proxy disabled so I can repair and
refresh the dataset?

$ env -u all_proxy -u http_proxy -u https_proxy ./.venv/bin/python - <<'PY'
import akshare as ak
from quant.fetch_utils import _fetch_em, fetch_range
try:
    df = ak.stock_zh_a_hist(symbol='600519', period='daily', start_date='20240101', end_date='20241231', adjust='hfq')
    print('ak', df.shape)
    if not df.empty:
        print(df.head(2).to_string())
        print(df.tail(2).to_string())
except Exception as e:
    print('ak_err', repr(e))
try:
    df = _fetch_em('600519','20240101','20241231',fqt=2)
    print('em', len(df), None if df.empty else (df.index.min(), df.index.max()))
except Exception as e:
    print('em_err', repr(e))
try:
    df = fetch_range('600519','20240101','20241231',adjust='hfq')
    print('fetch_range', len(df), None if df.empty else (df.index.min(), df.index.max()))
except Exception as e:
    print('fetch_range_err', repr(e))
PY

› 1. Yes, proceed (y)
  2. No, and tell Codex what to do differently (esc)"""

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "y")

    def test_detects_codex_menu_with_yes_hotkey(self) -> None:
        text = """Would you like to run the following command?

Reason: Do you want me to install the baostock package outside the sandbox so I can test an alternate stock data source and try to repair the
update pipeline?

$ ./.venv/bin/pip install baostock

› 1. Yes, proceed (y)
  2. Yes, and don't ask again for commands that start with `./.venv/bin/pip install` (p)
  3. No, and tell Codex what to do differently (esc)"""

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "y")

    def test_codex_menu_prefers_enter_when_prompt_says_press_enter(self) -> None:
        text = """Would you like to run the following command?

Reason: Do you want me to test AkShare's Sina A-share daily endpoint outside the sandbox as a fallback?

$ env -u all_proxy -u http_proxy -u https_proxy ./.venv/bin/python - <<'PY'
import akshare as ak
for symbol in ['sh600519','sz000001','sz300750']:
    for adjust in ['', 'qfq', 'hfq']:
        try:
            df = ak.stock_zh_a_daily(symbol=symbol, start_date='20240101', end_date='20241231', adjust=adjust)
            print(symbol, adjust or 'raw', df.shape)
        except Exception as e:
            print(symbol, adjust or 'raw', 'ERR', repr(e))
PY

› 1. Yes, proceed (y)
  2. No, and tell Codex what to do differently (esc)
Press enter to confirm or esc to cancel"""

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_codex_crontab_menu_prefers_enter_when_prompt_says_press_enter(self) -> None:
        text = """Would you like to run the following command?

Reason: Do you want me to install the updated user crontab with the new daily 8:00 PM xiaomi_trader job?

$ crontab /private/tmp/xiaomi_trader_crontab.txt

› 1. Yes, proceed (y)
  2. Yes, and don't ask again for commands that start with `crontab` (p)
  3. No, and tell Codex what to do differently (esc)
Press enter to confirm or esc to cancel"""

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_menu_drawn_with_ansi_cursor_down(self) -> None:
        text = (
            "Would you like to run the following command?\x1b[1B"
            "Reason: Do you want me to install the updated user crontab?\x1b[1B"
            "$ crontab /private/tmp/xiaomi_trader_crontab.txt\x1b[2B"
            "› 1. Yes, proceed (y)\x1b[1B"
            "  2. Yes, and don't ask again for commands that start with `crontab` (p)\x1b[1B"
            "  3. No, and tell Codex what to do differently (esc)\x1b[1B"
            "Press enter to confirm or esc to cancel"
        )

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "")

    def test_detects_menu_after_long_command_block(self) -> None:
        body = "\n".join(f"line {index}" for index in range(90))
        text = (
            "Would you like to run the following command?\n"
            "Reason: Do you want me to run a long generated script?\n"
            "$ python - <<'PY'\n"
            f"{body}\n"
            "PY\n"
            "› 1. Yes, proceed (y)\n"
            "  2. No, and tell Codex what to do differently (esc)"
        )

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "y")

    def test_detects_menu_drawn_with_ansi_cursor_up_and_clear_line(self) -> None:
        text = (
            "Would you like to run the following command?\n"
            "$ echo ok\n"
            "\x1b[2A\x1b[2K› 1. Yes, proceed (y)\n"
            "\x1b[2K  2. No, and tell Codex what to do differently (esc)"
        )

        match = find_confirmation(text)

        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.rule_name, "ai-cli-yes-choice")
        self.assertEqual(match.answer, "y")

    def test_latest_shell_command_extracts_codex_dollar_command(self) -> None:
        text = "Would you like to run the following command?\n$ git status --short\n1. Yes\n2. No"

        command = latest_shell_command(text)

        self.assertEqual(command, "git status --short")

    def test_does_not_confirm_menu_when_yes_is_not_first_choice(self) -> None:
        text = "Confirm operation\n1. No\n2. Yes"

        match = find_confirmation(text)

        self.assertIsNone(match)

    def test_does_not_confirm_bare_numbered_yes_no_list(self) -> None:
        text = "Options:\n1. Yes\n2. No"

        match = find_confirmation(text)

        self.assertIsNone(match)

    def test_does_not_treat_bare_run_as_confirmation_context(self) -> None:
        text = "npm run build\nOptions:\n1. Yes\n2. No"

        match = find_confirmation(text)

        self.assertIsNone(match)

    def test_does_not_confirm_sentence_containing_yes_and_no(self) -> None:
        text = "Confirm the docs mention yes and no in prose."

        match = find_confirmation(text)

        self.assertIsNone(match)

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
