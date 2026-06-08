## Why

FileGlide is positioned as an agent-oriented filesystem CLI, but its current text editing path is not reliable enough for complex real-world agent writes. Multi-line replacements can collapse adjacent lines, shell-passed HTML and quoted content can break argument parsing, and Windows non-ASCII write paths can succeed structurally while still corrupting visible content.

The project already claims precise editing, common encoding support, and strong non-ASCII handling. Those promises now need a concrete implementation upgrade so agents can safely edit Chinese-friendly, mixed-language, and structured text files without relying on fragile shell escaping or manual read-back repair.

## What Changes

- Harden text editing semantics so line-range replacement preserves exact line boundaries by default instead of depending on caller-supplied trailing newlines.
- Add robust content input channels for text and binary writes, including file-backed and stdin-backed content sources, so agents are not forced to pass large or quoted payloads through argv.
- Upgrade text serialization to preserve or explicitly control charset, BOM, and newline style during writes.
- Add write-time verification and safer write orchestration for text mutations that must remain stable after disk round-trip.
- Expand the CLI contract and regression coverage for HTML-like content, Windows non-ASCII content, and precise editing edge cases.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `content-read-write-editing`: strengthen precise text editing semantics, add alternate content input sources, and define newline-preserving replacement behavior.
- `encoding-and-binary-compatibility`: preserve charset and BOM intent during writes, improve non-ASCII safety, and validate final serialized bytes rather than string-only round trips.
- `batch-execution-and-json-output`: expose new content input and verification metadata through stable JSON results where write behavior changes are observable.

## Impact

- Affected code: `fileglide/commands/text.py`, `fileglide/services/text.py`, `fileglide/services/encoding.py`, executor/result metadata, and related batch dispatch wiring.
- Affected behavior: text write, line replacement, anchor insertion, binary write input modes, and JSON write metadata.
- Affected tests: CLI regression tests for line replacement, content transport, encoding preservation, BOM handling, and Windows-oriented non-ASCII write scenarios.
- No new product area is introduced, but existing text and encoding capabilities gain stronger behavioral guarantees and stricter verification.
