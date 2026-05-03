from __future__ import annotations

from collections import deque
import codecs
from dataclasses import dataclass
import os
import subprocess
import sys
import time

from .config import AyeConfig
from .detectors import BlockedCommandMatch, PromptMatch, find_blocked_command, find_confirmation, latest_shell_command, shell_commands

ENTER_CONFIRM_DELAY_SECONDS = 0.4
ENTER_RETRY_DELAYS_SECONDS = (1.0, 3.0)
ROLLING_OUTPUT_MIN_LINES = 240


def run_wrapped_command(
    command: list[str],
    config: AyeConfig,
    *,
    dry_run: bool = False,
    exit_on_idle: float | None = None,
    fifo: bool = False,
    verbose: bool = False,
) -> int:
    if not command:
        raise ValueError("No command provided to wrap.")

    if os.name == "posix":
        return _run_posix_pty(
            command,
            config,
            dry_run=dry_run,
            exit_on_idle=exit_on_idle,
            fifo=fifo,
            verbose=verbose,
        )
    return _run_pipe_fallback(command, config, dry_run=dry_run, verbose=verbose)


def _run_posix_pty(
    command: list[str],
    config: AyeConfig,
    *,
    dry_run: bool,
    exit_on_idle: float | None,
    fifo: bool,
    verbose: bool,
) -> int:
    import pty
    import selectors
    import termios
    import tty

    master_fd, slave_fd = pty.openpty()
    _copy_terminal_size(master_fd)
    process = subprocess.Popen(command, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd)
    os.close(slave_fd)

    selector = selectors.DefaultSelector()
    selector.register(master_fd, selectors.EVENT_READ)

    stdin_fd = sys.stdin.fileno()
    old_stdin_attrs = None
    if sys.stdin.isatty():
        old_stdin_attrs = termios.tcgetattr(stdin_fd)
        tty.setraw(stdin_fd)
        selector.register(stdin_fd, selectors.EVENT_READ)

    fifo_path = None
    fifo_fd = None
    if fifo:
        fifo_path, fifo_fd = _open_fifo()
        selector.register(fifo_fd, selectors.EVENT_READ)

    rolling_output = RollingTextBuffer(max_lines=max(config.scan_lines * 8, ROLLING_OUTPUT_MIN_LINES))
    detector = ConfirmationResponder(config=config, dry_run=dry_run, verbose=verbose)
    last_activity_at = time.monotonic()

    try:
        while process.poll() is None:
            for key, _ in selector.select(timeout=0.1):
                if key.fileobj == master_fd:
                    chunk = _read_available(master_fd)
                    if not chunk:
                        continue
                    sys.stdout.buffer.write(chunk)
                    sys.stdout.buffer.flush()
                    rolling_output.append_bytes(chunk)
                    detector.note_output()
                    detector.maybe_blocked(rolling_output.text)
                    detector.maybe_confirm(master_fd, rolling_output.text)
                    last_activity_at = time.monotonic()
                elif key.fileobj == stdin_fd:
                    user_input = _read_available(stdin_fd)
                    if user_input:
                        detector.clear_blocked()
                        os.write(master_fd, user_input)
                        last_activity_at = time.monotonic()
                elif key.fileobj == fifo_fd:
                    fifo_input = _read_available(fifo_fd)
                    if fifo_input:
                        detector.clear_blocked()
                        os.write(master_fd, fifo_input)
                        last_activity_at = time.monotonic()
            detector.maybe_retry(master_fd)
            if exit_on_idle is not None and time.monotonic() - last_activity_at >= exit_on_idle:
                print(f"\n[aye] Idle for {exit_on_idle:g}s, exiting.", file=sys.stderr, flush=True)
                _terminate_process(process)
                break
        return process.wait()
    finally:
        if old_stdin_attrs is not None:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_stdin_attrs)
        selector.close()
        try:
            os.close(master_fd)
        except OSError:
            pass
        if fifo_fd is not None:
            try:
                os.close(fifo_fd)
            except OSError:
                pass
        if fifo_path is not None:
            try:
                os.unlink(fifo_path)
            except OSError:
                pass


def _run_pipe_fallback(command: list[str], config: AyeConfig, *, dry_run: bool, verbose: bool) -> int:
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=0,
    )
    assert process.stdout is not None
    assert process.stdin is not None

    rolling_output = RollingTextBuffer(max_lines=max(config.scan_lines * 8, ROLLING_OUTPUT_MIN_LINES))
    detector = ConfirmationResponder(config=config, dry_run=dry_run, verbose=verbose)

    while True:
        chunk = process.stdout.read(4096)
        if not chunk:
            break
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()
        rolling_output.append_bytes(chunk)
        detector.note_output()
        detector.maybe_blocked(rolling_output.text)
        detector.maybe_confirm(process.stdin, rolling_output.text)

    return process.wait()


@dataclass
class PendingEnterRetry:
    signature: tuple[str, str]
    next_retry_at: float
    attempts: int = 0


class ConfirmationResponder:
    def __init__(self, *, config: AyeConfig, dry_run: bool, verbose: bool = False) -> None:
        self.config = config
        self.dry_run = dry_run
        self.verbose = verbose
        self.last_action_at = 0.0
        self.last_signature: tuple[str, str] | None = None
        self.last_blocked_signature: tuple[str, str] | None = None
        self.blocked_until_manual_input = False
        self.last_shell_command: str | None = None
        self.pending_enter_retry: PendingEnterRetry | None = None

    def maybe_confirm(self, target, text: str) -> None:
        match = find_confirmation(text, self.config.rules, scan_lines=self.config.scan_lines)
        if match is None:
            return

        if self.blocked_until_manual_input:
            return

        command = latest_shell_command(text)
        blocked = find_blocked_command(command, scan_lines=0) if command is not None else find_blocked_command(text, scan_lines=0)
        if blocked is not None:
            self._report_blocked(blocked)
            self.blocked_until_manual_input = True
            return

        if not self._should_answer(match):
            return

        if self.verbose:
            print(_describe_match(match, dry_run=self.dry_run), file=sys.stderr, flush=True)
        if not self.dry_run:
            if match.answer == "":
                time.sleep(ENTER_CONFIRM_DELAY_SECONDS)
            _write_answer(target, match.answer)
        self.last_action_at = time.monotonic()
        self.last_signature = (match.rule_name, match.excerpt)
        self._schedule_enter_retry(match)

    def note_output(self) -> None:
        self.pending_enter_retry = None

    def maybe_retry(self, target) -> None:
        retry = self.pending_enter_retry
        if retry is None or time.monotonic() < retry.next_retry_at:
            return
        if self.verbose:
            print(_describe_enter_retry(retry), file=sys.stderr, flush=True)
        if not self.dry_run:
            _write_answer(target, "")
        retry.attempts += 1
        if retry.attempts >= len(ENTER_RETRY_DELAYS_SECONDS):
            self.pending_enter_retry = None
            return
        retry.next_retry_at = time.monotonic() + ENTER_RETRY_DELAYS_SECONDS[retry.attempts]

    def maybe_blocked(self, text: str) -> bool:
        # Path 1: text contains extracted Bash(...) commands — check each one
        # individually so that a new safe command clears a previous block.
        commands = shell_commands(text)
        if commands:
            return self._check_extracted_commands(commands)

        # Path 2: no structured Bash(...) pattern found; fall back to scanning
        # the full text against blocked-command rules.  Guard against re-checking
        # the same raw text that was already processed.
        if text == self.last_shell_command:
            return self.blocked_until_manual_input
        blocked_command = find_blocked_command(text, scan_lines=self.config.scan_lines)
        if blocked_command is None:
            return False
        self._report_blocked(blocked_command)
        self.blocked_until_manual_input = True
        return True

    def _check_extracted_commands(self, commands: list[str]) -> bool:
        """Check each extracted shell command for dangerous patterns.

        The last command in the list determines the final blocked state:
        if the most recent command is safe, we clear the block so the
        responder can auto-confirm the next prompt.
        """
        for command in commands:
            if command == self.last_shell_command:
                continue
            self.last_shell_command = command
            blocked_command = find_blocked_command(command, scan_lines=0)
            if blocked_command is None:
                self.blocked_until_manual_input = False
                continue
            self._report_blocked(blocked_command)
            self.blocked_until_manual_input = True
        return self.blocked_until_manual_input

    def clear_blocked(self) -> None:
        self.blocked_until_manual_input = False
        self.pending_enter_retry = None

    def _report_blocked(self, match: BlockedCommandMatch) -> None:
        signature = (match.rule_name, match.excerpt)
        if signature == self.last_blocked_signature:
            return
        if self.verbose:
            print(_describe_blocked(match), file=sys.stderr, flush=True)
        self.last_blocked_signature = signature

    def _should_answer(self, match: PromptMatch) -> bool:
        signature = (match.rule_name, match.excerpt)
        if signature == self.last_signature:
            return False
        if self.last_signature is not None and match.rule_name == self.last_signature[0]:
            previous_excerpt = self.last_signature[1]
            if previous_excerpt in match.excerpt or match.excerpt in previous_excerpt:
                return False
        return True

    def _schedule_enter_retry(self, match: PromptMatch) -> None:
        if self.dry_run or match.answer != "":
            self.pending_enter_retry = None
            return
        self.pending_enter_retry = PendingEnterRetry(
            signature=(match.rule_name, match.excerpt),
            next_retry_at=time.monotonic() + ENTER_RETRY_DELAYS_SECONDS[0],
        )


class RollingTextBuffer:
    def __init__(self, *, max_lines: int) -> None:
        self.max_lines = max_lines
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._lines: deque[str] = deque(maxlen=max_lines)
        self._partial = ""

    @property
    def text(self) -> str:
        return "\n".join([*self._lines, self._partial])

    def append_bytes(self, chunk: bytes) -> str:
        decoded = self._decoder.decode(chunk)
        if not decoded:
            return ""
        parts = decoded.splitlines(keepends=True)
        for part in parts:
            self._append_text(part)
        return decoded

    def _append_text(self, text: str) -> None:
        self._partial += text
        while "\n" in self._partial:
            line, self._partial = self._partial.split("\n", 1)
            self._lines.append(line)


def _read_available(fd: int) -> bytes:
    try:
        return os.read(fd, 4096)
    except OSError:
        return b""


def _open_fifo() -> tuple[str, int]:
    path = f"/tmp/aye-{time.strftime('%Y%m%d%H%M%S')}-{os.getpid()}.stdin"
    os.mkfifo(path, 0o600)
    fd = os.open(path, os.O_RDWR | os.O_NONBLOCK)
    print(f"[aye] FIFO input: {path}", file=sys.stderr, flush=True)
    return path, fd


def _terminate_process(process: subprocess.Popen) -> None:
    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


def _write_answer(target, answer: str) -> None:
    payload = f"{answer}\r".encode()
    if isinstance(target, int):
        os.write(target, payload)
        return
    target.write(payload)
    target.flush()


def _describe_match(match: PromptMatch, *, dry_run: bool) -> str:
    mode = "DRY RUN match" if dry_run else "Auto-confirming"
    return f"{mode}: rule={match.rule_name} answer={match.answer!r} excerpt={match.excerpt!r}"


def _describe_blocked(match: BlockedCommandMatch) -> str:
    return f"Blocked auto-confirm: dangerous_command={match.rule_name!r} excerpt={match.excerpt!r}"


def _describe_enter_retry(retry: PendingEnterRetry) -> str:
    return f"Retrying auto-confirm enter: attempt={retry.attempts + 1} rule={retry.signature[0]}"


def _copy_terminal_size(fd: int) -> None:
    if not sys.stdin.isatty():
        return
    try:
        import fcntl
        import termios

        size = fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, b"\0" * 8)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, size)
    except OSError:
        return
