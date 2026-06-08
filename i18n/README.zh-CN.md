<div align="center">
  <h1>FileGlide</h1>
  <p><strong>面向 AI agent 的文件系统 CLI，提供精确、中文友好的文件与路径操作，并具备更强的非 ASCII 支持。</strong></p>
  <p>从统一命令树中完成树遍历、大小感知、名称与内容检索、精确行编辑、二进制处理，以及显式批量计划执行。</p>
  <p>
    <a href="https://www.python.org/"><img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-2F5D8C"></a>
    <a href="https://pypi.org/project/click/"><img alt="CLI framework Click" src="https://img.shields.io/badge/CLI-Click-2563EB"></a>
    <a href="https://pypi.org/project/vortezwohl/"><img alt="Fuzzy matching vortezwohl" src="https://img.shields.io/badge/Fuzzy-vortezwohl-0F766E"></a>
    <a href="../docs/fileglide-architecture.html"><img alt="Architecture HTML" src="https://img.shields.io/badge/Docs-Architecture-9A3412"></a>
  </p>
  <p>
    <a href="#安装">安装</a> |
    <a href="#快速开始">快速开始</a> |
    <a href="#命令树">命令树</a> |
    <a href="#输出与编码">输出与编码</a> |
    <a href="#检索与编辑">检索与编辑</a> |
    <a href="#批量执行">批量执行</a> |
    <a href="#更多文档">更多文档</a>
  </p>
</div>

<p align="center"><strong><a href="../README.md">English</a> | 简体中文 | <a href="README.zh-TW.md">繁體中文</a></strong></p>

## 安装

安装完成后，直接使用正式 CLI 入口即可：

```powershell
fileglide --help
```

需要 Python `3.10+`。CLI 基于 `click` 构建，默认输出契约为 JSON。

## 快速开始

### 1. 创建受控工作区目录

```powershell
fileglide path create 'tests/tmp/demo/docs' --root 'D:\github-project\fileglide' --parents --exist-ok
```

通过 `--root` 可以把所有相对路径约束在一个明确的工作区根目录下。

### 2. 创建并写入文本文件

```powershell
fileglide file create 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --parents --exist-ok
fileglide text write 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --mode overwrite --content "alpha`nbravo`ncharlie"
```

可以通过 `overwrite`、`append`、`insert` 三种模式控制文本写入行为。

### 3. 精确读取行区间

```powershell
fileglide text read 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --start-line 2 --end-line 3
```

当 agent 只需要局部上下文而不想整文件载入时，这种精确读取很有用。

### 4. 用正则检索文件内容

```powershell
fileglide text grep 'bravo|charlie' 'tests/tmp/demo' --root 'D:\github-project\fileglide' --include '*.txt'
```

内容检索支持正则表达式和局部范围遍历。

### 5. 模糊检索文件名

```powershell
fileglide file search 'note' 'tests/tmp/demo' --root 'D:\github-project\fileglide' --mode fuzzy
```

文件名和路径名的模糊匹配基于 `vortezwohl` 的莱温斯坦距离能力实现。

## 命令树

| 命令 | 角色 | 典型用途 |
|---|---|---|
| `file` | 文件生命周期与文件级遍历 | 创建、删除、列举、存在性判断、文件检索 |
| `path` | 目录生命周期与路径级遍历 | 创建、删除、列举、存在性判断、目录检索 |
| `tree` | 混合树遍历 | 从受控起点同时返回文件和目录 |
| `text` | 文本与二进制内容操作 | 读取、写入、正则检索、行区间替换、锚点插入、二进制复制 |
| `inspect` | 大小与字节检查 | 获取文件/目录大小，读取二进制安全的字节片段 |
| `batch` | 显式批量执行 | 校验并逐步执行 JSON 计划 |

## 输出与编码

当前对外默认行为：

- `--format json`
- `--pretty`
- 通过 `--root` 做受控路径解析
- 直接适配 UTF-8 without BOM
- 文本工作流可识别并处理 UTF-8 BOM、UTF-16 LE、GBK、GB18030、Shift-JIS 等常见编码
- 二进制命令保持二进制安全，不强行按文本解码

实践建议：

- 人工查看时可切换到 `--format text`。
- 脚本、自动化、agent 调用优先保持 `json`。
- 文本命令可通过 `--encoding` 强制指定编码。
- 二进制写入与字节切片检查可以避免非文本数据被误损坏。

## 检索与编辑

代表性编辑与检索操作：

```powershell
fileglide text write 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --mode append --content "`ndelta"
fileglide text write 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --mode insert --position 6 --content '[INSERT]'
fileglide text replace-lines 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --start-line 2 --end-line 2 --content 'BRAVO'
fileglide text insert-anchor 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --after --anchor 'BRAVO' --content "`nANCHOR-INSERT"
```

```powershell
fileglide path search 'doc' 'tests/tmp/demo' --root 'D:\github-project\fileglide' --mode fuzzy --kind directory
fileglide tree list 'tests/tmp/demo' --root 'D:\github-project\fileglide' --kind all
fileglide inspect size 'tests/tmp/demo' --root 'D:\github-project\fileglide'
```

这些命令面向 AI agent 设计，目标是让文件系统操作具备精确、本地、可验证的行为，而不是依赖脆弱的 shell 文本解析。

## 批量执行

`fileglide` 支持用显式 JSON 计划组织一组操作。

计划示例结构：

```json
{
  "steps": [
    {
      "action": "path.create",
      "params": {
        "target": "tests/tmp/batch-demo",
        "root": "D:\\github-project\\fileglide",
        "parents": true,
        "exist_ok": true
      }
    },
    {
      "action": "text.write",
      "params": {
        "target": "tests/tmp/batch-demo/readme.txt",
        "root": "D:\\github-project\\fileglide",
        "mode": "overwrite",
        "content": "batch-ready"
      }
    }
  ]
}
```

建议先预览，再执行：

```powershell
fileglide batch run 'D:\github-project\fileglide\tests\fixtures\batch\sample-plan.json' --dry-run
fileglide batch run 'D:\github-project\fileglide\tests\fixtures\batch\sample-plan.json' --apply
```

## 更多文档

- [架构与项目设计](../docs/fileglide-architecture.html)
- [English README](../README.md)
- [繁體中文 README](README.zh-TW.md)

## License

MIT License.