# Aye

Aye 是一个给 AI 编程 CLI 用的自动确认工具。名字读起来就是 “yes”。它会在同一个终端里启动 Claude Code、Gemini CLI、Codex 等命令，持续观察输出，遇到明确确认提示时自动输入 `yes`、`y` 或回车。

它不监控外部终端窗口，只包装自己启动的命令，所以适合本地终端，也适合远端服务器。

## 下载使用

到 GitHub Releases 下载对应平台的文件：

- `aye-linux-x64.tar.gz`
- `aye-linux-arm64.tar.gz`
- `aye-darwin-x64.tar.gz`
- `aye-darwin-arm64.tar.gz`

实际文件名会包含版本号，例如 `aye-v0.0.2-darwin-arm64.tar.gz`。

Linux x64：

```sh
tar -xzf aye-v0.0.2-linux-x64.tar.gz
chmod +x aye
./aye claude
```

Linux ARM64 把文件名换成 `aye-v0.0.2-linux-arm64.tar.gz`。

macOS Apple Silicon：

```sh
tar -xzf aye-v0.0.2-darwin-arm64.tar.gz
chmod +x aye
./aye claude
```

macOS Intel 把文件名换成 `aye-v0.0.2-darwin-x64.tar.gz`。

如果 macOS 提示无法打开下载的文件，先移除 quarantine 标记：

```sh
xattr -d com.apple.quarantine aye
```

需要放到远端服务器长期使用时，把 `aye` 放进 `PATH` 即可：

```sh
sudo mv aye /usr/local/bin/aye
aye claude
```

## 常用命令

默认启动 `claude`：

```sh
aye
```

也可以包装 Gemini CLI 或 Codex：

```sh
aye gemini
aye codex
```

传递原 CLI 参数：

```sh
aye claude --model sonnet
aye gemini --model gemini-2.5-pro
aye codex --model gpt-5
```

Aye 会用伪终端运行目标命令，所以被包装的 CLI 仍然保持交互式体验。你可以正常输入，也可以用 `Ctrl+C` 中断。

查看版本：

```sh
aye --version
```

更新到 GitHub Releases 里的最新版本：

```sh
aye update
```

Claude 官方也支持 `--dangerously-skip-permissions` 参数；如果你的场景可以接受它的风险，推荐优先使用官方命令行能力。

## 配置

一般不需要配置。只有当你想调整匹配范围、冷却时间或自定义确认提示规则时，才需要生成配置文件：

```sh
aye init-config aye.json
```

使用配置运行：

```sh
aye --config aye.json claude
```

完整配置项见 [配置说明](docs/config.md)。

## 安全提醒

不要在高风险仓库或生产环境里无脑开启自动确认。它会真的替你按确认，可能导致命令执行、文件修改、部署、删除或费用消耗。

Aye 内置了一层删除命令拦截：最近输出里出现 `rm`、`rmdir`、`unlink` 时，即使命中确认提示，也不会自动输入确认。
