# 错题笔记与 Anki 卡片生成

将代码错误、修复对比和源码学习材料整理为 Markdown、Mermaid 与 Anki TSV。

**当前为模拟版。所有示例岗位、项目贡献、错误和环境状态均为虚构教学素材；没有连接个人工作流，也没有实际投递、导入笔记库或修复现场环境。**

## 安装

将整个仓库作为一个 Skill 目录放到 `$CODEX_HOME/skills/code-sandbox-anki-generator`；未设置 CODEX_HOME 时使用 `~/.codex/skills/code-sandbox-anki-generator`。先检查同名目录，避免覆盖。仓库根目录的 `SKILL.md` 是技能入口，`agents/openai.yaml` 提供 UI 元数据。

Windows 的命令统一使用 PowerShell 7（`pwsh`），不调用 Windows PowerShell 5.1。辅助 Python 脚本需要 Python 3.11+，仅使用标准库。仓库中的 examples/tests 不是新的 Skill。

## 调用示例

```text
使用 $code-sandbox-anki-generator，根据 examples/note-input.json 生成模拟笔记与 Anki TSV，保留未验证标记。
```

## 工作方式与范围

渲染器只格式化已提供的证据，不推断缺失的原始报错或修复历史。输出不覆盖已有同名文件；Anki TSV 是可导入文件，不等于已导入卡片库。

```powershell
python -X utf8 scripts/render_note.py examples/note-input.json --output-dir run-notes --name reshape --anki
```

首次运行创建文件；重复运行需选择新目录或名称。Typora、Anki 与桌面整理软件尚未接通。

## 示例与验证

演示材料见 [examples/](examples/)，技能详情见 [SKILL.md](SKILL.md)。包含 2 项对应辅助脚本的行为测试，只使用临时目录与模拟数据。

```powershell
python -X utf8 -B -m unittest discover -s tests -v
```

四个 Skill 均通过结构校验。仓库测试仅说明列出的模拟行为；browser-use、Typora、Anki 导入、MCP 注册和现场 CUDA 等集成并未验证。此版本不把静态源码、文档关键词或模拟输入当作用户真实成果。
