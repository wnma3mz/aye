# Security Policy

Aye automatically answers terminal prompts. Use it only in repositories and environments you trust.

## Reporting

Please report security issues privately by opening a GitHub security advisory on:

https://github.com/wnma3mz/aye/security/advisories/new

If GitHub advisories are unavailable, open a minimal issue that does not include exploit details.

## Safety Defaults

- Aye matches explicit prompt text only.
- Aye checks only recent terminal output.
- Aye blocks auto-confirmation when recent output includes `rm`, `rmdir`, or `unlink`.
- Aye does not use an LLM to decide whether a prompt is safe.
