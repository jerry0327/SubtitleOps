# Governance

SubtitleOps is an independently maintained open-source project. The repository owner, [@jerry0327](https://github.com/jerry0327), is the current primary maintainer and release manager.

## Roles

### Primary maintainer

The primary maintainer is responsible for:

- repository scope and architecture;
- issue triage and release planning;
- review and merge decisions;
- security coordination;
- compatibility of the CLI, Python API, configuration, diagnostics, JSON, and SARIF contracts;
- assigning or revoking maintainer access.

### Contributors

Anyone may propose an issue, documentation change, test, or pull request. A contribution does not create an ongoing maintenance obligation. Contributors retain attribution through Git history.

### Additional maintainers

Sustained contributors may be invited to become maintainers after demonstrating sound technical judgment, respectful collaboration, and familiarity with the project's compatibility and security constraints. Maintainer status is based on repeated work, not a single contribution.

## Decision process

Most decisions are made through public issues and pull requests. The primary maintainer seeks the smallest change that solves a documented user or maintenance problem.

For non-trivial changes, the expected record is:

1. a problem statement or linked issue;
2. tests for observable behavior;
3. documentation and changelog updates when user-facing contracts change;
4. passing CI and security checks;
5. an explicit merge decision.

The primary maintainer has final decision authority while the project has one maintainer. Security reports and embargoed fixes may be handled privately until coordinated disclosure is appropriate.

## Compatibility policy

SubtitleOps is pre-1.0. Minor releases may refine APIs and defaults, but changes to stable diagnostic codes, exit codes, JSON schema versions, SARIF behavior, or configuration keys require explicit compatibility notes. Silent repurposing of a diagnostic code is not allowed.

## Release policy

Releases are created from a green `main` branch through the tag-driven release workflow. Published version tags and attached artifacts are immutable. Release preparation and rollback rules are documented in [docs/releasing.md](docs/releasing.md).

## Maintenance expectations

The project provides no commercial SLA. The maintainer uses the following best-effort targets:

- acknowledge actionable bug and security reports within seven days;
- triage ordinary issues and pull requests within fourteen days;
- keep supported-branch CI and CodeQL results visible;
- document prolonged maintenance pauses in the repository.

These are operating targets, not guaranteed response times.

## Inactivity and succession

If the primary maintainer expects to be unavailable for more than 60 days, the repository should state that status. If another contributor has demonstrated sustained maintenance work, ownership or release responsibilities may be delegated explicitly. No contributor should infer maintainer authority from inactivity alone.

## Conduct

All project spaces follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security reports follow [SECURITY.md](SECURITY.md).
