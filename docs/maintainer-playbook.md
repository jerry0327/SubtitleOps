# Maintainer playbook

This playbook turns repository policy into repeatable maintenance work. It is intentionally usable by a single maintainer and can be expanded if additional maintainers join.

## Issue triage

For each new issue:

1. classify it as bug, feature, format/interoperability, documentation, adoption, or security;
2. confirm that private or copyrighted subtitle content has not been posted unnecessarily;
3. request a minimized reproducer and exact version/configuration;
4. identify the affected contract: parser, rule, CLI, API, configuration, JSON, SARIF, action, or packaging;
5. close duplicates with a link to the canonical issue;
6. state whether the report is accepted, needs information, is out of scope, or belongs on the roadmap.

Security-sensitive reports move to the process in `SECURITY.md`.

## Pull-request review

A reviewer checks:

- the problem is documented and in scope;
- observable behavior has focused tests;
- deterministic ordering and cross-platform paths are preserved;
- mutation does not discard unsupported structure silently;
- new diagnostic codes have metadata and rule documentation;
- JSON/SARIF/configuration/API compatibility is addressed;
- runtime dependency cost is justified;
- user-facing changes appear in the changelog;
- CI and CodeQL complete successfully.

A green check is necessary but not sufficient for merge.

## Dependency updates

Dependabot pull requests are reviewed rather than merged solely because they are automated. For a major action update:

1. inspect upstream release notes and breaking behavior;
2. verify that workflow permissions remain minimal;
3. require CI and CodeQL success;
4. merge one overlapping update at a time or supersede conflicting PRs explicitly;
5. record any behavior change in project documentation when relevant.

## Release checklist

1. confirm the package and module versions match;
2. confirm the changelog has a dated section;
3. review open release-blocking issues;
4. require green CI and CodeQL on `main`;
5. create the immutable semantic version tag;
6. verify the release workflow tests, builds, smoke-installs, checksums, and publishes artifacts;
7. verify the floating major action tag points to the release commit;
8. perform a post-release install/action smoke check;
9. open follow-up issues rather than silently altering a published tag.

See [releasing](releasing.md) for commands and failure handling.

## Monthly maintenance review

- review untriaged issues and stale pull requests;
- inspect Dependabot and CodeQL results;
- verify documentation examples still pin supported action versions;
- review roadmap priorities against user reports;
- check whether security or support policies need clarification;
- record maintenance pauses or deprecations publicly.

## AI-assisted maintenance boundaries

AI assistants may be used to:

- draft regression tests and minimized synthetic fixtures;
- identify likely compatibility surfaces in a proposed change;
- summarize upstream dependency release notes;
- draft issue triage notes, release notes, and migration guidance;
- propose code for review in an isolated branch.

They must not independently:

- merge or release without maintainer review;
- disclose a vulnerability;
- invent adoption, usage, contributor, or performance claims;
- rewrite user subtitle content as part of the deterministic runtime;
- treat generated tests as proof without executing them.

The maintainer remains accountable for every merged change and published statement.
