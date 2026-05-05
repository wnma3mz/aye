# 配置说明

Aye 默认不需要配置。配置文件只用于收窄或扩展自动确认规则。

生成默认配置：

```sh
aye init-config aye.json
```

使用配置：

```sh
aye --config aye.json claude
```

## 配置项

`scan_lines`：只检查终端最近多少行输出。默认是 `20`。数值越小越保守，越不容易误匹配旧内容。

`cooldown_seconds`：保留的兼容配置项。当前默认会尽量确认每一个命中的提示，不再用全局冷却时间跳过连续确认。

`dedupe_repeated_prompts`：是否跳过重复确认提示。默认是 `false`，也就是同一个提示重复出现时仍会继续自动确认。设为 `true` 后，Aye 会跳过单纯 TUI 重绘造成的重复提示；如果上次回答后又出现新的确认提示，则仍会再次确认。

`rules`：确认提示匹配规则。每条规则包含：

- `name`：规则名称，只用于日志。
- `pattern`：Python 正则表达式。
- `answer`：命中后输入的内容。设为空字符串 `""` 时，只按回车。

## 示例

```json
{
  "scan_lines": 20,
  "cooldown_seconds": 8.0,
  "dedupe_repeated_prompts": false,
  "rules": [
    {
      "name": "explicit-type-yes",
      "pattern": "(type|enter)\\s+['\\\"]?yes['\\\"]?\\s+to\\s+(continue|proceed|confirm)",
      "answer": "yes"
    },
    {
      "name": "ai-cli-permission-yes",
      "pattern": "(do you want to|would you like to).{0,80}(continue|proceed|allow|run|execute).{0,80}\\byes\\b",
      "answer": "yes"
    },
    {
      "name": "ai-cli-permission-yn",
      "pattern": "((allow|approve).{0,80}(run|execute|command|tool|shell|edit|write)|(run|execute|command|tool|shell|edit|write).{0,80}(allow|approve|confirm)).{0,80}(\\[y/N\\]|\\(y/N\\)|\\by/n\\b)",
      "answer": "y"
    },
    {
      "name": "ai-cli-yes-choice",
      "pattern": "(^|\\n)\\s*(?:[^\\w\\s]\\s*)?\\[?1[.)\\]]\\s*yes\\b[\\s\\S]{0,600}\\n\\s*(?:[^\\w\\s]\\s*)?\\[?\\d+[.)\\]]\\s*no\\b",
      "answer": ""
    }
  ]
}
```

## 注意

自定义规则会替换默认规则。建议先复制 `aye init-config` 生成的默认配置，再按需删改。

删除命令拦截规则不在配置文件里开放。Aye 始终会拦截最近输出里的 `rm`、`rmdir`、`unlink`，避免自动确认明显危险的删除操作。
