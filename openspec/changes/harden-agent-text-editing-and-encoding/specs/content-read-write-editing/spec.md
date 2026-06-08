## MODIFIED Requirements

### Requirement: Overwrite, Append, and Insert Writes
The system SHALL support overwrite writes, tail append writes, and middle insert writes for both text and binary workflows where applicable, and text writes SHALL accept payloads from inline content, file-backed content, or stdin-backed content.

#### Scenario: Overwrite a text file
- **WHEN** the caller performs an overwrite write on a text file
- **THEN** the system SHALL replace the full content and report before/after size and write status in JSON

#### Scenario: Append binary content
- **WHEN** the caller appends binary data to an existing binary file
- **THEN** the system SHALL preserve existing bytes, append the new bytes, and return a successful binary write result

#### Scenario: Write HTML content from stdin
- **WHEN** the caller provides multi-line HTML content through stdin for a text write
- **THEN** the system SHALL persist the exact content without requiring shell-level escaping of the payload body

#### Scenario: Write multilingual content from a content file
- **WHEN** the caller provides Chinese, Japanese, or other non-ASCII text through a file-backed content source
- **THEN** the system SHALL persist the exact characters without replacing them with placeholder characters introduced by argv transport

### Requirement: Precise Editing by Line, Range, and Anchor
The system SHALL support precise editing of text files by line number, line range, text range, and anchor-based insertion or replacement, and SHALL preserve surrounding logical line boundaries by default when the replacement content does not explicitly redefine them.

#### Scenario: Replace a line range
- **WHEN** the caller replaces a specific line range in a text file
- **THEN** the system returns the changed range, diff-oriented metadata, and write result in JSON

#### Scenario: Insert content after an anchor
- **WHEN** the caller requests insertion after a unique anchor match
- **THEN** the system SHALL insert content at the resolved location and report the anchor resolution result

#### Scenario: Replace a middle line without a trailing newline
- **WHEN** the caller replaces a middle line range and the replacement content does not end with a newline character
- **THEN** the system SHALL preserve the next logical line as a distinct line instead of merging it into the replacement line

#### Scenario: Preserve file newline style during line replacement
- **WHEN** the caller performs a line-range replacement without an explicit newline override
- **THEN** the system SHALL serialize the edited file using the existing file newline style by default
