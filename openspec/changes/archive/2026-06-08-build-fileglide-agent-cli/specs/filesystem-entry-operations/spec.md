## ADDED Requirements

### Requirement: File and Path Lifecycle Operations
The system SHALL provide CLI commands to create and delete files and paths within a caller-defined scope.

#### Scenario: Create a file in a scoped root
- **WHEN** the caller requests file creation with a target path under the allowed root
- **THEN** the system returns a successful JSON result containing the created file path and creation status

#### Scenario: Delete a directory tree in dry-run mode
- **WHEN** the caller requests recursive path deletion with `dry-run` enabled
- **THEN** the system SHALL not delete any filesystem entries and SHALL return a JSON preview of affected targets

### Requirement: File and Path Traversal
The system SHALL support global and local traversal for files and paths with explicit scope, recursion, and depth controls.

#### Scenario: Traverse files under a local root
- **WHEN** the caller requests file traversal with a local root and recursion enabled
- **THEN** the system returns JSON records for matching files including relative path, kind, and size metadata

#### Scenario: Limit traversal depth
- **WHEN** the caller specifies a maximum depth for traversal
- **THEN** the system SHALL exclude entries deeper than the requested depth from the result set

### Requirement: File and Path Size Awareness
The system SHALL report file sizes and aggregated path sizes for both text and binary entries.

#### Scenario: Get a single file size
- **WHEN** the caller requests file size information for an existing file
- **THEN** the system returns the byte size and normalized path metadata in JSON

#### Scenario: Get aggregated directory size
- **WHEN** the caller requests path size for a directory
- **THEN** the system SHALL aggregate descendant entry sizes and return the total byte count in JSON