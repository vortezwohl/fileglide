## MODIFIED Requirements

### Requirement: UTF-8 Without BOM Preferred Write Strategy
The system SHALL prefer UTF-8 without BOM for new text files unless the caller explicitly selects another encoding, and SHALL preserve an existing file BOM when the caller does not explicitly override BOM policy.

#### Scenario: Create a new text file without encoding override
- **WHEN** the caller writes a new text file without specifying encoding
- **THEN** the system SHALL encode the file as UTF-8 without BOM and report the encoding in JSON metadata

#### Scenario: Rewrite a BOM-backed file without override
- **WHEN** the caller edits an existing text file that already uses a BOM-backed encoding and does not request a different write policy
- **THEN** the system SHALL preserve the existing BOM behavior during serialization and report it in write metadata

### Requirement: Common Encoding Compatibility
The system SHALL detect or honor explicit encoding for common text encodings including UTF-8, UTF-8 BOM, GBK, GB18030, Shift-JIS, and UTF-16 variants, and SHALL validate the final serialized bytes before reporting a successful text write.

#### Scenario: Read a GBK-encoded text file
- **WHEN** the caller reads a GBK-encoded file without forcing the wrong encoding
- **THEN** the system SHALL decode the text successfully and report the encoding decision in JSON

#### Scenario: Warn on lossy write risk
- **WHEN** the caller requests a write that cannot be losslessly encoded in the target encoding
- **THEN** the system SHALL return a structured warning or error before committing the write

#### Scenario: Verify final multilingual write bytes
- **WHEN** the caller writes multilingual non-ASCII content through the text workflow
- **THEN** the system SHALL verify the final serialized bytes written to disk before reporting success
