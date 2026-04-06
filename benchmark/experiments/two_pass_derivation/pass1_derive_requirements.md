# Task: Derive Testable Requirements for NSQ Subsystems

You are a quality engineer performing a requirements derivation exercise. Your goal is to read NSQ's documentation and source structure, then produce a list of testable requirements for two specific subsystems. You have NO knowledge of any specific bugs or defects — you are deriving requirements from documentation only.

## Documentation Sources

Read these files to understand NSQ's design, features, and intended behavior:

1. `README.md` — Project overview, features, guarantees
2. `ChangeLog.md` — Release notes documenting features, behaviors, and design decisions
3. `nsqd/options.go` — Configuration struct with all fields, defaults, and field types
4. `nsqd/nsqd.go` — Main NSQD type, initialization (New function), startup, and shutdown
5. `nsqd/guid.go` — GUID generation, bit layout, worker ID encoding
6. `internal/auth/authorizations.go` — Auth server client, authorization queries

## Subsystems to Analyze

### Subsystem 1: NSQD Configuration and Startup
Files: `nsqd/nsqd.go`, `nsqd/options.go`, `nsqd/guid.go`

Focus on: How configuration values are parsed, validated, and used during initialization. How the worker ID is encoded in the GUID format. What constraints exist on configuration fields based on their types, ranges, and downstream usage.

### Subsystem 2: TLS and Authentication Path
Files: `nsqd/nsqd.go` (TLS configuration and setup), `internal/auth/authorizations.go`

Focus on: How TLS is configured for inbound and outbound connections. How the auth server client is initialized. Whether security configuration (certificates, CA files) is consistently applied across all connection types.

## Requirement Categories

For each subsystem, derive requirements in these categories. Not every category will apply to every subsystem — only include categories where you find signal in the documentation.

1. **Input Validation**: Configuration fields with domain constraints (numeric ranges, valid values, type constraints). Any field where invalid input could produce silent incorrect behavior rather than an error.

2. **Security Policy Propagation**: Security settings (TLS, certificates, authentication) that must be consistently applied across all code paths. Any place where a security configuration could fail to propagate to a connection or operation.

3. **Resource Lifecycle**: Initialization ordering, cleanup sequences, connection management. Any resource that must be properly started/stopped.

4. **API Contracts**: Guarantees about how components interact. Bit layouts, protocol negotiation, field encoding.

## Instructions

For each requirement you derive:

1. State the requirement as a testable assertion (e.g., "X must satisfy Y" or "When A, the system must B")
2. Cite the documentation source that supports the requirement (file, line, or ChangeLog entry)
3. Rate the requirement's specificity: **specific** (testable against a single code location) or **directional** (guides an audit but doesn't point to one location)

Organize requirements by subsystem, then by category.

Do NOT review the code for bugs. Do NOT run or test anything. Your only job is to derive requirements from what the documentation tells you about intended behavior.

## Output

Save your requirements to a file called `requirements_raw.md` in the current directory.
