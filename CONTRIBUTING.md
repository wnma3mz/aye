# Contributing

Thanks for improving Aye.

## Development

```sh
uv sync --group build
uv run python -m unittest discover -s tests
```

## Build

```sh
uv run --group build python scripts/build.py --clean
```

## Guidelines

- Keep the public CLI simple: `aye`, `aye claude`, `aye gemini`, `aye codex`.
- Keep automatic confirmation rule-based and conservative.
- Add or update tests when changing prompt detection or terminal interaction.
- Update `README.md` for user-visible behavior changes.
