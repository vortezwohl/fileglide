## Context

FileGlide already exposes text reads, text writes, line-range replacement, anchor insertion, binary writes, and encoding detection. The current implementation is lightweight: text reads decode the file into a Python string, and edits rebuild the file by slicing and joining strings. That keeps the code small, but it leaves three reliability gaps visible in agent usage.

First, precise line replacement currently depends on caller-supplied line endings. If replacement content omits a trailing newline while replacing a middle line, the next preserved line can be merged into the same logical line. Second, the CLI only accepts write payloads through `--content`, which means complex HTML, quotes, multi-line blocks, and mixed-language text must survive the outer shell argv boundary. Third, encoding validation currently proves that a Python string can round-trip through a charset, but it does not prove that the final on-disk bytes preserve BOM state, newline style, or the intended serialized representation.

The design has to preserve FileGlide's current direction: default JSON output, explicit local filesystem behavior, binary-safe routing, and no background service. The change should improve correctness without turning the CLI into a heavyweight editor or introducing an unnecessary dependency stack.

## Goals / Non-Goals

**Goals:**
- Make line-range replacement stable for middle-of-file edits even when replacement content omits trailing newlines.
- Let callers provide text and binary payloads through more reliable channels than argv-only `--content` / `--data-hex`.
- Preserve or explicitly control charset, BOM, and newline style during text writes.
- Add write-time verification that checks the final serialized bytes written to disk.
- Keep the public CLI and JSON result structure evolvable without breaking the existing command tree.

**Non-Goals:**
- Do not introduce a GUI, editor integration protocol, or daemonized background process.
- Do not add AST-aware or language-aware semantic editing in this change.
- Do not replace Click or redesign the entire command tree.
- Do not attempt to guarantee perfect automatic encoding detection for every legacy encoding; the focus is safe transport and safe write-back.

## Decisions

### Decision 1: Introduce a unified content source layer
The CLI should support multiple payload origins for text and binary writes: direct inline content, file-backed content, stdin-backed content, and binary base64 or file input where appropriate.

Rationale:
- This removes the current over-reliance on shell argv escaping for HTML, quotes, and non-ASCII content.
- It matches how agents actually work: they often materialize content into temp files or pipe content between tools.
- It keeps the write surface explicit without inventing a higher-level natural language plan format.

Alternatives considered:
- Keep argv-only payloads and document escaping rules. Rejected because it does not materially improve reliability.
- Add only `--content-file` but no stdin. Rejected because stdin remains the most natural transport for generated payloads in chained automation.

### Decision 2: Replace raw split-and-join edits with a text document model
Text mutations should operate on a small internal document model that tracks logical lines, line endings, final newline state, charset, and BOM.

Rationale:
- The current `splitlines(keepends=True)` approach is too easy to misuse and pushes newline correctness onto the caller.
- A document model lets FileGlide define `preserve` semantics clearly: replacement of a middle line range should keep the surrounding file's newline boundaries unless the caller explicitly overrides them.
- The same model can support line reads, line replacements, anchor insertions, and future text-range edits without each command re-implementing newline heuristics.

Alternatives considered:
- Patch `replace_lines` with ad hoc newline fixes. Rejected because it solves only one symptom and will regress again in anchor insertion and future edit modes.
- Depend on a third-party text buffer library. Rejected because the required behavior is small enough to own locally.

### Decision 3: Separate charset choice from BOM policy and newline policy
Encoding decisions should be represented as three explicit write concerns: charset, BOM policy, and newline policy.

Rationale:
- `utf-8-sig` and UTF-16 BOM handling are serialization concerns, not just decode labels.
- The current `encoding_for_write` API is too coarse; it cannot express "write UTF-16 LE with BOM preserved" or "reuse existing charset but normalize newlines to LF" as first-class policy.
- Explicit policy objects make result metadata and testing much clearer.

Alternatives considered:
- Continue using a single encoding string and infer BOM implicitly. Rejected because it obscures write behavior and can silently drop BOM state.

### Decision 4: Move verification to final serialized bytes
Write validation should operate on the exact bytes that will be persisted, not only on string encode/decode round trips.

Rationale:
- String round-trip success does not prove BOM preservation, newline preservation, or byte-for-byte serialization intent.
- For agent workflows, "command returned ok" is not enough; the system should verify its own on-disk result before reporting success.
- Byte-level verification also gives better metadata for batch execution and audit trails.

Alternatives considered:
- Keep current validation and rely on caller read-back. Rejected because the tool itself should guarantee stronger correctness before claiming success.

### Decision 5: Prefer overwrite-via-serialized-bytes plus atomic replace
All text write paths should produce final bytes, write them to a temp file in the same directory, and atomically replace the target.

Rationale:
- This limits partial-write risk and makes verification simpler.
- It unifies overwrite, append, insert, and replace-lines around one final serialization path.
- Same-directory atomic replace is a pragmatic default for local filesystem safety.

Alternatives considered:
- Continue using `Path.write_text()` directly. Rejected because it hides newline translation details and gives less control over exact bytes.

## Risks / Trade-offs

- [Risk] More write modes and content source options can complicate command help and testing. -> Mitigation: keep inline content as the default path and document file/stdin modes as reliability upgrades for complex content.
- [Risk] A document model adds complexity to a currently small service. -> Mitigation: keep the model narrowly scoped to line boundaries, final newline state, BOM, and charset; avoid building a general editor framework.
- [Risk] Byte-level verification adds extra I/O. -> Mitigation: scope verification to write commands only and reuse the same bytes buffer for checksum and size reporting.
- [Risk] Backward compatibility may be affected if callers implicitly relied on the old broken newline-merging behavior. -> Mitigation: define `preserve` as the new default and offer explicit newline policy flags for advanced callers.

## Migration Plan

1. Add content source parsing to the text and binary command layer while keeping existing inline options intact.
2. Introduce the internal text document model and route `replace-lines` and anchor insertion through it first.
3. Refactor overwrite, append, and insert text writes to serialize through the new charset/BOM/newline policy path.
4. Add atomic write and byte-level verification metadata.
5. Expand CLI regression tests and fixture coverage before enabling any behavior marked as default.
6. Update docs and examples to recommend file/stdin payload transport for complex or multilingual content.

Rollback strategy:
- The implementation can be staged so content source support lands before the editing kernel rewrite.
- If verification uncovers unacceptable regressions, the code can temporarily retain old write entry points behind the facade while the document model stays internal and incomplete.

## Open Questions

- Should binary payload transport add both `--data-file` and `--data-base64`, or is `--data-file` plus stdin sufficient for the first pass?
- Should newline policy be exposed immediately as a public CLI option, or should the first implementation keep it internal with `preserve` only?
- Do we want JSON results to include checksums by default for every write, or only when verification or verbose output is enabled?
