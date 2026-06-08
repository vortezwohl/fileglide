# content-read-write-editing Specification

## Purpose
TBD - created by archiving change build-fileglide-agent-cli. Update Purpose after archive.
## Requirements
### Requirement: Text and Binary Read Operations
The system SHALL support reading full content, slices, line ranges, and binary byte ranges through CLI commands.

#### Scenario: Read a text file by line range
- **WHEN** the caller requests a specific line range from a text file
- **THEN** the system returns the selected lines, line numbers, encoding metadata, and path metadata in JSON

#### Scenario: Read a binary slice by byte range
- **WHEN** the caller requests a byte range from a binary file
- **THEN** the system returns the exact byte slice metadata and a binary-safe JSON representation

### Requirement: Overwrite, Append, and Insert Writes
The system SHALL support overwrite writes, tail append writes, and middle insert writes for both text and binary workflows where applicable.

#### Scenario: Overwrite a text file
- **WHEN** the caller performs an overwrite write on a text file
- **THEN** the system SHALL replace the full content and report before/after size and write status in JSON

#### Scenario: Append binary content
- **WHEN** the caller appends binary data to an existing binary file
- **THEN** the system SHALL preserve existing bytes, append the new bytes, and return a successful binary write result

### Requirement: Precise Editing by Line, Range, and Anchor
The system SHALL support precise editing of text files by line number, line range, text range, and anchor-based insertion or replacement.

#### Scenario: Replace a line range
- **WHEN** the caller replaces a specific line range in a text file
- **THEN** the system returns the changed range, diff-oriented metadata, and write result in JSON

#### Scenario: Insert content after an anchor
- **WHEN** the caller requests insertion after a unique anchor match
- **THEN** the system SHALL insert content at the resolved location and report the anchor resolution result

