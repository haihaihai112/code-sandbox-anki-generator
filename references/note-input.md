# 渲染器输入契约

`render_note.py` 需要 Python 3.11+，仅使用标准库。必填 `title`、`date`（用户日期 ISO YYYY-MM-DD）、`topic`。可选正文项缺失时显示“未提供”，不补造内容。

| 字段 | 类型与含义 |
|---|---|
| `sources` | 字符串数组：材料来源和范围，模拟时写“模拟案例；非学习历史”，并注明素材是否虚构 |
| `context`, `error`, `before`, `after`, `cause`, `verification` | 字符串或 null。验证内容说明是否运行及实际结果 |
| `language` | 代码块语言，默认 python；SQL/TS 等可改 |
| `takeaways` | 字符串数组，一般知识与项目结论区分 |
| `flow.nodes` | 数组：每项 `id` 为 `[A-Za-z][A-Za-z0-9_]*`、`label` 为非空字符串 |
| `flow.edges` | 数组：每项为已定义两个 node id 组成的数组 |
| `cards` | 数组：每项 `front`、`back` 非空字符串，`tags` 可选字符串数组（单词，无空白） |

完整虚构样例见 [examples/note-input.json](../examples/note-input.json)。该样例不是用户学习历史，也不是运行必需的输入；可按上表自建 JSON。

CLI `--name` 是不含路径的 ASCII slug；渲染器自动加日期前缀。代码块会选择足够长的围栏以容纳原始反引号；Anki TSV 将正文转义成 HTML，每行三列 `Front / Back / Tags`，内置导入头。导入 Anki 时选 Basic（正反面），检查字段映射和“允许 HTML”；不生成 `.apkg`，不自动改卡片库。

渲染器不推断错误原因，也不自动脱敏任意代码。生成输入 JSON 的代理需先脱敏并核对所有内容。未提供 Mermaid 数据时明确没有图，而不是制造虚构处理流程。
