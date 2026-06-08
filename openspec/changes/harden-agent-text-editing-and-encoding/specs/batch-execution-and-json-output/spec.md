## MODIFIED Requirements

### Requirement: Structured Error and Warning Reporting
The system SHALL provide structured warnings and errors for single commands and batch commands, and write operations SHALL return structured metadata for content source, charset, BOM, newline policy, and write verification when those behaviors are relevant.

#### Scenario: Return a structured validation error
- **WHEN** the caller provides invalid command parameters or plan content
- **THEN** the system returns a JSON error object with machine-readable type and human-readable detail

#### Scenario: Report verified text write metadata
- **WHEN** the caller performs a text write, line replacement, or anchor insertion
- **THEN** the system SHALL return structured metadata indicating the selected content source, final charset, BOM behavior, newline behavior, and whether final write verification succeeded
