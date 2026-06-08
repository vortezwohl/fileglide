## ADDED Requirements

### Requirement: UTF-8 Without BOM Preferred Write Strategy
The system SHALL prefer UTF-8 without BOM for new text files unless the caller explicitly selects another encoding.

#### Scenario: Create a new text file without encoding override
- **WHEN** the caller writes a new text file without specifying encoding
- **THEN** the system SHALL encode the file as UTF-8 without BOM and report the encoding in JSON metadata

### Requirement: Common Encoding Compatibility
The system SHALL detect or honor explicit encoding for common text encodings including UTF-8, UTF-8 BOM, GBK, GB18030, Shift-JIS, and UTF-16 variants.

#### Scenario: Read a GBK-encoded text file
- **WHEN** the caller reads a GBK-encoded file without forcing the wrong encoding
- **THEN** the system SHALL decode the text successfully and report the encoding decision in JSON

#### Scenario: Warn on lossy write risk
- **WHEN** the caller requests a write that cannot be losslessly encoded in the target encoding
- **THEN** the system SHALL return a structured warning or error before committing the write

### Requirement: Binary-Safe Operation Routing
The system SHALL distinguish text workflows from binary workflows and SHALL avoid implicit text decoding for binary operations.

#### Scenario: Copy binary bytes without decoding
- **WHEN** the caller performs a binary read and binary write workflow
- **THEN** the system SHALL preserve byte identity without attempting text decoding