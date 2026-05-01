# CLAUDE.md

本文件用于约束 Claude / 其他编码代理在本项目中的行为。先遵守“项目规则”，再遵守后面的通用编码准则。

## 项目规则

### 项目定位

Aye 是一个轻量的 AI 编程 CLI 包装器。核心诉求是：在同一个终端里启动 Claude Code、Gemini CLI、Codex 等命令，持续观察输出，遇到明确确认提示时自动输入 `yes`、`y` 或回车。

### 范围边界

- 只维护直接包装启动路径，例如 `aye claude`、`aye gemini`、`aye codex`。
- 不恢复 macOS 外部终端监控能力。
- 不新增 Terminal.app / iTerm2 / AppleScript 相关逻辑。
- 不把项目扩成多 CLI 平台框架，除非用户明确要求。
- 不引入 Docker、后台服务、守护进程、复杂崩溃恢复，除非用户明确要求。

### 技术约束

- 使用 `uv` 管理环境、依赖、测试和构建。
- 依赖声明放在 `pyproject.toml`。
- 构建命令使用 `uv run --group build python scripts/build.py --clean`。
- 测试命令使用 `uv run python -m unittest discover -s tests`。
- README 使用中文。
- 新增或修改用户可见行为时，同步更新 README。

### 实现原则

- 优先保持实现轻量，围绕 `consent_pilot/wrapper.py` 和显式规则匹配演进。
- 自动确认逻辑必须基于明确的文本规则，不要引入 LLM 判断。
- 修改提示匹配规则时，补充或更新 `tests/test_detectors.py`。
- 修改包装器交互、输入输出行为时，补充或更新 `tests/test_wrapper.py`。
- 避免误触高风险确认。宁可匹配保守，也不要扩大到模糊意图。

### 验证标准

改动完成后至少运行：

```sh
uv run python -m unittest discover -s tests
```

如果改了包装器主流程，再运行一个冒烟测试：

```sh
uv run aye sh -c 'printf "Type yes to continue\n"; read answer; printf "answer=%s\n" "$answer"'
```

## 通用编码准则

以下内容来自 https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/refs/heads/main/CLAUDE.md ，作为本项目的基础代理行为准则。

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
