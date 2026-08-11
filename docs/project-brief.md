# Project brief

## Summary

SubtitleOps is a deterministic, dependency-light quality gate for text subtitle assets. It validates SRT, WebVTT, and a conservative TTML/DFXP subset; produces human-readable, JSON, and SARIF reports; and integrates with local scripts or GitHub Actions.

The project sits between transcription/localization and publication. It is intended for generated-caption checks, localization handoffs, media repositories, documentation/video pipelines, and release gates where reproducible findings matter more than opaque scoring.

## Problem

Subtitle files are often generated or edited by several tools before publication. Defects can remain invisible until late in a release:

- reversed or overlapping timing;
- unreadable display duration or character rate;
- malformed timestamps or documents;
- line and whitespace problems;
- conversion that silently drops unsupported structure;
- CI systems that cannot consume a stable diagnostic contract.

General-purpose linters rarely understand subtitle timing. Media tools may validate only the container or syntax, and many subtitle editors are interactive rather than automation-first.

## Approach

SubtitleOps uses explicit rules and deterministic parsers rather than a model call at runtime. The same input, configuration, and version should produce the same ordered findings. The project treats exit codes, rule IDs, JSON, SARIF, and conservative mutation behavior as public product surfaces.

Key design choices are:

- no speech recognition, translation, or dialogue rewriting;
- bounded file reads by default;
- per-file isolation during batch checks;
- rejection of TTML constructs that cannot be represented safely;
- preservation of WebVTT document blocks during same-format repair;
- minimal runtime dependencies.

## Intended users

- open-source projects that publish videos or training material;
- localization and accessibility teams with repository-based workflows;
- transcription pipelines that need a deterministic post-processing gate;
- developers building subtitle QA or reporting integrations;
- maintainers who need SARIF-compatible findings in code review.

## Current maintenance evidence

The repository includes:

- reviewed pull-request history;
- CI across supported Python versions, plus Windows and macOS smoke coverage;
- CodeQL analysis;
- unit, integration, action, packaging, and clean-install checks;
- Dependabot configuration and dependency triage;
- an issue template set, security policy, code of conduct, governance, roadmap, and support policy;
- a tag-driven release workflow with checksums and immutable release artifacts.

## Public adoption status

SubtitleOps is newly public. It does not claim external adopters, download volume, stars, or ecosystem-critical status without public evidence. The adoption issue form exists so users can report integrations that can be verified and used to guide priorities.

## Six-month maintenance objectives

1. Establish a predictable release cadence and exercise the release/security playbooks.
2. Add baseline and diff-aware checking for established repositories.
3. Collect minimized real-world parser and interoperability cases.
4. Document at least one complete external adoption path, subject to a user's permission.
5. Measure performance on a redistributable synthetic/public corpus.
6. Define the compatibility requirements for a future 1.0 release.

## Responsible automation

AI-assisted development may help draft tests, minimize reproducers, compare specifications, review compatibility implications, and prepare release notes. A human maintainer remains responsible for scope, security disclosure, merge decisions, and releases. Generated changes must pass the same review and CI requirements as any other contribution.

See [architecture](design.md), [maintainer playbook](maintainer-playbook.md), [roadmap](../ROADMAP.md), and [governance](../GOVERNANCE.md).
