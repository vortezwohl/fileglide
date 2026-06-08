## 1. CLI Content Transport

- [x] 1.1 Add a shared content-source parser for text commands that supports inline content, file-backed content, and stdin-backed content.
- [x] 1.2 Extend binary write input handling with non-argv payload transport suitable for larger or non-hex workflows.
- [x] 1.3 Update command validation so incompatible payload source combinations fail with structured errors.

## 2. Text Editing Core

- [x] 2.1 Introduce an internal text document model that tracks logical lines, newline style, final newline state, charset, and BOM metadata.
- [x] 2.2 Refactor line-range replacement to preserve surrounding line boundaries by default when replacement content omits a trailing newline.
- [x] 2.3 Route anchor insertion and text insert mode through the same document serialization path to avoid divergent newline behavior.

## 3. Encoding and Serialization

- [x] 3.1 Split write policy concerns into charset selection, BOM handling, and newline handling.
- [x] 3.2 Replace direct `Path.write_text()` calls with explicit byte serialization plus atomic file replacement.
- [x] 3.3 Add final-byte verification and structured write metadata for text mutation commands.

## 4. Regression Coverage

- [x] 4.1 Add tests for middle-line replacement without trailing newlines under LF and CRLF files.
- [x] 4.2 Add tests for HTML-like quoted payloads and multilingual non-ASCII payloads using file/stdin content transport.
- [x] 4.3 Add tests for BOM-preserving rewrites and verified write metadata in JSON responses.