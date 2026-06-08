# search-and-matching Specification

## Purpose
TBD - created by archiving change build-fileglide-agent-cli. Update Purpose after archive.
## Requirements
### Requirement: Path and File Search Modes
The system SHALL support exact, contains, scoped, and fuzzy search for file names and paths.

#### Scenario: Exact file name search
- **WHEN** the caller searches for a file by exact name under a scoped root
- **THEN** the system returns only exact matches with normalized path metadata in JSON

#### Scenario: Fuzzy path search
- **WHEN** the caller performs fuzzy search for a path or file name
- **THEN** the system SHALL rank candidates using `vortezwohl` Levenshtein distance and include score metadata in JSON

### Requirement: Regex Content Search
The system SHALL support regex-based content retrieval for text files with line-aware hit reporting.

#### Scenario: Regex match in a text file
- **WHEN** the caller searches file content with a valid regular expression
- **THEN** the system returns matching path, line number, preview, and matcher metadata in JSON

#### Scenario: Invalid regex input
- **WHEN** the caller provides an invalid regular expression
- **THEN** the system SHALL return a structured error without scanning files

### Requirement: Search Scope and Filtering Controls
The system SHALL enforce root scope, include filters, exclude filters, recursion flags, and depth limits during search.

#### Scenario: Search with include and exclude filters
- **WHEN** the caller searches within a scoped root using include and exclude patterns
- **THEN** the system SHALL only scan files that satisfy the filtering rules and report the applied scope metadata

