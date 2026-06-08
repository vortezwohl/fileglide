<div align="center">
  <h1>FileGlide</h1>
  <p><strong>面向 AI agent 的檔案系統 CLI，提供精確、中文友好的檔案與路徑操作，並具備更強的非 ASCII 支援。</strong></p>
  <p>從統一命令樹中完成樹狀遍歷、大小感知、名稱與內容檢索、精確行編輯、二進位處理，以及顯式批次計畫執行。</p>
  <p>
    <a href="https://www.python.org/"><img alt="Python 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-2F5D8C"></a>
    <a href="https://pypi.org/project/click/"><img alt="CLI framework Click" src="https://img.shields.io/badge/CLI-Click-2563EB"></a>
    <a href="https://pypi.org/project/vortezwohl/"><img alt="Fuzzy matching vortezwohl" src="https://img.shields.io/badge/Fuzzy-vortezwohl-0F766E"></a>
    <a href="../docs/fileglide-architecture.html"><img alt="Architecture HTML" src="https://img.shields.io/badge/Docs-Architecture-9A3412"></a>
  </p>
  <p>
    <a href="#安裝">安裝</a> |
    <a href="#agent-skills">Agent Skills</a> |
    <a href="#快速開始">快速開始</a> |
    <a href="#命令樹">命令樹</a> |
    <a href="#輸出與編碼">輸出與編碼</a> |
    <a href="#檢索與編輯">檢索與編輯</a> |
    <a href="#批次執行">批次執行</a> |
    <a href="#更多文件">更多文件</a>
  </p>
</div>

<p align="center"><strong><a href="../README.md">English</a> | <a href="README.zh-CN.md">简体中文</a> | 繁體中文</strong></p>

## 安裝

安裝已發佈到 PyPI 的 `fileglide`。安裝完成後會直接提供 `fileglide` CLI。

```powershell
uv add -U fileglide
fileglide --help
```

```powershell
pip install -U fileglide
fileglide --help
```

執行環境需求為 Python `3.10+`。CLI 基於 `click` 建構，預設對外輸出契約為 JSON。

## Agent Skills

FileGlide 也提供了 agent skill，可供 Codex、Claude Code 與其他 coding agent 使用。

當你希望 agent 幫你安裝這些 skill 時，只需要直接說：

> Please install skills from `https://github.com/vortezwohl/fileglide`, and place them in my global user skill directory.

這些 skill 主要面向受約束檔案系統存取、精確文字編輯、OpenSpec 變更流程，以及可驗證的分步執行工作流。

## 快速開始

### 1. 建立受控工作區目錄

```powershell
fileglide path create 'tests/tmp/demo/docs' --root 'D:\github-project\fileglide' --parents --exist-ok
```

透過 `--root` 可以把所有相對路徑約束在一個明確的工作區根目錄下。

### 2. 建立並寫入文字檔案

```powershell
fileglide file create 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --parents --exist-ok
fileglide text write 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --mode overwrite --content "alpha`nbravo`ncharlie"
```

可以透過 `overwrite`、`append`、`insert` 三種模式控制文字寫入行為。

### 3. 精確讀取行區間

```powershell
fileglide text read 'tests/tmp/demo/docs/notes.txt' --root 'D:\github-project\fileglide' --start-line 2 --end-line 3
```

當 agent 只需要局部上下文而不想整個檔案載入時，這種精確讀取很有用。

### 4. 以正則檢索檔案內容

```powershell
fileglide text grep 'bravo|charlie' 'tests/tmp/demo' --root 'D:\github-project\fileglide' --include '*.txt'
```

內容檢索支援正則表達式與局部範圍遍歷。

### 5. 模糊檢索檔名

```powershell
fileglide file search 'note' 'tests/tmp/demo' --root 'D:\github-project\fileglide' --mode fuzzy
```

檔名與路徑名的模糊比對基於 `vortezwohl` 的萊文斯坦距離能力實作。

## 命令樹

| 命令 | 角色 | 典型用途 |
|---|---|---|
| `file` | 檔案生命週期與檔案級遍歷 | 建立、刪除、列出、存在性判斷、檔案檢索 |
| `path` | 目錄生命週期與路徑級遍歷 | 建立、刪除、列出、存在性判斷、目錄檢索 |
| `tree` | 混合樹狀遍歷 | 從受控起點同時回傳檔案與目錄 |
| `text` | 文字與二進位內容操作 | 讀取、寫入、正則檢索、行區間替換、錨點插入、二進位複製 |
| `inspect` | 大小與位元組檢查 | 取得檔案/目錄大小，讀取二進位安全的位元組片段 |
| `batch` | 顯式批次執行 | 驗證並逐步執行 JSON 計畫 |

## 輸出與編碼

目前對外預設行為：

- `--format json`
- `--pretty`
- 透過 `--root` 做受控路徑解析
- 直接適配 UTF-8 without BOM
- 文字工作流程可識別並處理 UTF-8 BOM、UTF-16 LE、GBK、GB18030、Shift-JIS 等常見編碼
- 二進位命令保持二進位安全，不強制按文字解碼

實務建議：

- 人工檢視時可切換為 `--format text`。
- 腳本、自動化、agent 呼叫優先保持 `json`。
- 文字命令可透過 `--encoding` 強制指定編碼。
- 二進位寫入與位元組切片檢查可以避免非文字資料被誤毀損。

## 檢索與編輯

代表性的編輯與檢索操作：

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

這些命令是為 AI agent 設計，目標是讓檔案系統操作具備精確、本地、可驗證的行為，而不是依賴脆弱的 shell 文字解析。

## 批次執行

`fileglide` 支援以顯式 JSON 計畫組織一組操作。

計畫範例結構：

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

建議先預覽，再執行：

```powershell
fileglide batch run 'D:\github-project\fileglide\tests\fixtures\batch\sample-plan.json' --dry-run
fileglide batch run 'D:\github-project\fileglide\tests\fixtures\batch\sample-plan.json' --apply
```

## 更多文件

- [架構與專案設計](../docs/fileglide-architecture.html)
- [English README](../README.md)
- [简体中文 README](README.zh-CN.md)

## License

MIT License.