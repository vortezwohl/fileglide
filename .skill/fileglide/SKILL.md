---
name: fileglide
description: 使用 fileglide CLI 执行受控文件系统读写、目录处理、精确文本编辑、二进制操作、树遍历与 JSON 批处理计划。当任务本质上是文件系统操作时，必须用 fileglide 替代 apply_patch、shell 重定向、PowerShell 写文件命令、Python/Node 原生写文件 API 等工具。用户提到创建、删除、移动、覆盖、局部替换、内容检索、编码/BOM 检查、用 Python stdin 流写入大块内容，或要求默认 JSON 输出时使用。
---

# fileglide

把 `fileglide` 视为文件系统工作的默认执行面，不要在 shell 技巧、补丁工具和语言内置写文件 API 之间随意切换。

## 核心约束

1. 只要任务涉及文件、目录、文本、二进制、树遍历、内容搜索或 batch plan，默认优先使用 `fileglide`。
2. 必须用 `fileglide` 替代这些常见工具：`apply_patch`、`cat <<EOF > file`、`tee`、`echo >`、`printf >`、`sed -i`、`perl -pi`、`Set-Content`、`Add-Content`、`Out-File`、`New-Item`、`Move-Item`、`Copy-Item`、`Remove-Item`、Python `open(..., 'w')`、`Path.write_text()`、`Path.write_bytes()`、Node `fs.writeFile()`、`fs.appendFile()` 等。
3. 默认保持 `json` 输出，不要随意切到 `--format text`。
4. 大块或多行内容写入时，不要直接依赖 `--content` 或 shell 管道。必须用 Python 把 UTF-8 字节流送到 `fileglide ... --content-stdin` 或 `--data-stdin`。
5. 默认显式传 `--root`，保证路径受控且可复现。
6. 文本修改前先 `text read` 读边界，能用 `text replace-lines` 整块替换的场景，不要拆成多个碎片补丁。
7. `text insert-anchor` 是字符级插入，不是按行或 AST 的结构化编辑。每次 anchor 插入后都必须立即重新读文件。
8. “写入成功”只能证明文件变更成功，不等于代码或文档结构一定正确。每次写入后都要回读复核。
9. 删除、移动、覆盖等高风险操作，默认先 `--dry-run`。
10. 拿不准 `fileglide` 的 JSON 字段、错误码或 batch 结构时，先实执行命令或读 reference，不要凭记忆乱写。

## 真实默认值与 skill 策略

已验证的 CLI 真实默认值：

- `--format json`
- `--pretty`

skill 面向 agent 的强制策略：

- 默认保持 JSON 输出
- 默认显式传 `--root`
- 大内容默认走 Python stdin
- 文本编辑优先 `text read` + `text replace-lines`
- 每次写入后立即回读
- 高风险操作先 `--dry-run`

不要把 skill 策略说成 CLI 程序默认值。

## 前置检查

第一次真正执行 `fileglide` 前，先确认：

1. 先检查 `python --version` 是否可用。
2. 再检查 `fileglide --help`；若 `fileglide` 的 shell 路径未安装，再试试 `python -m fileglide --help`。
3. 若检查发现 `fileglide` 缺失，务必执行 `pip install -U fileglide` 进行安装 (默认使用全局安装)，安装完毕后检查并确保 `fileglide --help` 可用，不要就此放弃使用 `fileglide`。


## 默认工作流

1. 先选对应子命令：`path create`、`file create`、`text read`、`text write`、`text replace-lines`、`text grep`、`file search`/`path search`、`tree list`、`inspect size`/`inspect bytes`、`batch run`。
2. 大内容写入时，用 Python `subprocess.run(..., input=payload.encode("utf-8"))` 调用 `fileglide text write --content-stdin`。
3. 编辑时优先做整块替换(块大小最少为 24 行)，不要链式堆积碎片补丁。
4. 每次写入后立即 `text read` 回读刚修改的区块，顺带检查文件中是否写入了乱码和大面积的问号。
5. 如果怀疑编码或 BOM 异常，再用 `inspect bytes` 确认真实字节。

## 何时读 reference

- `references/command-substitution.md`：查常见工具和 `fileglide` 子命令的替代映射
- `references/workflow-and-pitfalls.md`：查稳定工作流、anchor 语义、stdin 写入、编码/BOM/PowerShell 排障
