# fileglide 稳定工作流与踩坑方法论

## 核心心智模型

`fileglide` 是低层、可验证、面向文件系统的精确工具，不是 AST 编辑器，也不会替你理解代码结构。

## 稳定工作流

1. 先 `text read` 读准边界，再决定怎么改。
2. 能整块替换就整块替换，默认优先 `text replace-lines`。
3. 大内容写入时，用 Python 发 UTF-8 字节到 `fileglide text write --content-stdin`。
4. 每次写入后立即回读。
5. 怀疑编码或 BOM 问题时，用 `inspect bytes` 查真实字节。

## `insert-anchor` 的正确理解

- 它是“在唯一 anchor 字符串前或后做字符级插入”。
- `--after` 意味着 anchor 字符串之后，不是“这一行之后”。
- 如果你需要新行，就要自己显式补换行。
- anchor 插入后必须立即重新读文件，不能沿用旧行号。
- 修改完整函数、类或 import 块时，通常应该用 `replace-lines`，不是 `insert-anchor`。

## Python stdin 写入模式

```python
import json
import subprocess

fileglide = r"D:\github-project\fileglide\.venv\Scripts\fileglide.exe"
root = r"D:\github-project\fileglide"
target = "docs/tmp/large.md"
payload = '''# 标题

这里是大块正文。
'''

command = [
    fileglide,
    "text",
    "write",
    "--root",
    root,
    "--mode",
    "overwrite",
    "--content-stdin",
    target,
]
completed = subprocess.run(
    command,
    input=payload.encode("utf-8"),
    capture_output=True,
    check=False,
)
response = json.loads(completed.stdout.decode("utf-8"))
if completed.returncode != 0:
    raise RuntimeError(response)
```

## 编码和 shell 层排障

- 多行正文、引号和特殊字符很容易在 shell 参数层先出问题，所以长正文默认不要走 `--content`。
- `invalid_text_content_source` 或 `binary_detected` 不一定是 `fileglide` bug，可能是 shell、BOM、编码或终端显示层的问题。
- 终端显示乱码不等于文件已损坏，先看 JSON 返回，再看 `inspect bytes`。
- 如果你看到大量 `?`，通常不是“显示错了”，而是某一层已经用不支持中文的编码做了替换回退；这种损坏往往不可逆。

## Windows / PowerShell 中文写入踩坑经验

- 在 Windows 下，`'中文' | some.exe` 往往比 `some.exe "中文"` 更脆弱。前者会穿过 PowerShell 管道、控制台编码和目标进程 stdin，任一层降级都可能把中文写成 `?`。
- 能用参数就不要用 stdin；能传文件路径就不要直接传大段正文；能传 UTF-8 文件、JSON 或 Base64，就不要让中文裸奔经过 shell 字符串流。
- 尽量避免把正文再转交给 `cmd /c`、`.bat`、`findstr` 或只认 OEM/ANSI 代码页的老工具；它们在代码页不一致时很容易把中文写坏。
- 只有在必须给原生命令喂 stdin 时，才把统一 `$OutputEncoding`、`[Console]::InputEncoding` 和 `[Console]::OutputEncoding` 当成兜底方案；这不是首选路径。
- 即使在 PowerShell 7，长正文默认也应优先走 Python `stdin -> fileglide --content-stdin`，因为这条链路只传 UTF-8 字节，边界更明确，也更容易回读复核。
- 本次把方法论写回 skill 文档本身，也遵循同一原则：不用 `Set-Content`、`Out-File` 或 shell 重定向，改用 Python UTF-8 stdin 驱动 `fileglide`，避免 Windows 文本流先把中文写坏。

## 方法论总结

- 先读清边界，再改
- 优先整块替换，不要碎片拼接
- 大内容统一走 Python UTF-8 stdin
- Windows 下优先避免让中文裸奔经过 shell / stdin 文本流
- 每次写完都立即回读
- 把文件写入成功、结构正确、语义正确分层验证
