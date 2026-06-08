## Why

需要一个面向 AI agent 的本地文件系统 CLI，让文件、路径、文本和二进制内容的读写、遍历、检索、精确编辑与批量执行都能通过稳定、结构化、可验证的接口完成。现在仓库只有初步设计文档，尚缺少可实施的 OpenSpec 变更方案，必须先把范围、能力边界和实施顺序固化下来，避免后续实现扩散失控。

## What Changes

- 新建 `fileglide` 的 CLI 变更方案，明确以 `click` 作为命令框架。
- 规定 CLI 默认输出为 `json`，同时保留适合人类查看的其他输出扩展空间。
- 设计文件与路径的创建、删除、遍历、搜索、检索、大小感知与结构化返回能力。
- 设计文本读写、追加、插入、按行和按区间精确编辑能力。
- 设计二进制内容读取、写入、切片、检索与复制能力，确保二进制文件不是被一律排除的特殊对象。
- 设计正则内容检索与基于 `vortezwohl` 的 Levenshtein 文件名/路径模糊匹配能力。
- 设计批量执行能力，包括计划文件、批量任务编排、预演、结果汇总与失败回报。
- 设计 UTF-8 without BOM 优先、兼容常见中文/日文及其他常见编码的解码与写回策略。

## Capabilities

### New Capabilities
- `filesystem-entry-operations`: 覆盖文件与路径的创建、删除、遍历、大小统计和作用域控制。
- `content-read-write-editing`: 覆盖文本与二进制内容的读取、覆盖写入、追加写入、插入写入、按行和按区间精确编辑。
- `search-and-matching`: 覆盖路径/文件搜索、正则内容检索、Levenshtein 模糊匹配和搜索结果排序。
- `batch-execution-and-json-output`: 覆盖默认 JSON 输出、批量执行计划、dry-run、批量结果汇总和 agent 友好输出契约。
- `encoding-and-binary-compatibility`: 覆盖 UTF-8 无 BOM 优先、常见编码兼容、二进制检测与二进制安全操作语义。

### Modified Capabilities
- None.

## Impact

- 新增 `fileglide` 包级 CLI 入口、命令树、执行器、门面层与领域服务层。
- 新增或扩展 `click` 命令定义、输出渲染、错误模型、编码服务、搜索匹配服务和批量执行服务。
- 持续依赖 `vortezwohl`，并以其 Levenshtein 能力作为模糊匹配默认实现。
- 需要在测试中引入文本、编码、二进制、目录树和批量任务样本夹具。
- 会影响未来 README、docs、OpenSpec specs、design、tasks 和实现排期。