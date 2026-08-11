# Roadmap

This roadmap communicates direction, not a promise of dates or funding. Priorities may change when real users report higher-impact problems.

## Current foundation: 0.3.x

The current line provides:

- deterministic SRT, WebVTT, and conservative TTML/DFXP checking;
- directory discovery and bounded concurrent processing;
- stable diagnostic codes and exit semantics;
- text, JSON schema v1, and SARIF 2.1.0 reporting;
- conservative fixes and cross-format conversion;
- a reusable GitHub Action;
- tested packaging, CodeQL, release automation, and documented security/maintenance processes.

## 0.4: adoption without a clean-slate migration

Primary objective: allow established subtitle repositories to introduce SubtitleOps without fixing every historical finding immediately.

Planned work:

- baseline files with deterministic fingerprints;
- compare-only-new or compare-changed findings;
- explicit baseline creation and update commands;
- CI documentation for staged enforcement;
- compatibility tests for path moves and cue renumbering.

## 0.5: profiles and operational scale

Planned work:

- named rule profiles for common publishing contexts;
- configuration composition with transparent precedence;
- a reproducible performance corpus containing only redistributable or synthetic text;
- benchmark reporting for discovery, parsing, linting, and SARIF generation;
- improved diagnostics for very large repositories.

## 0.6: format depth

Planned work:

- broader TTML profile coverage where semantics can be represented safely;
- additional WebVTT conformance diagnostics;
- investigation of EBU-TT and IMSC interoperability;
- explicit preservation or rejection rules for every newly accepted structure.

## 1.0 readiness criteria

SubtitleOps should not declare 1.0 solely because features exist. The target criteria are:

- documented stability commitments for the CLI and public Python API;
- a migration policy for JSON, SARIF, configuration, and diagnostic codes;
- release and security procedures exercised by multiple public releases;
- cross-platform CI remaining consistently green;
- at least one complete external adoption path documented from user feedback;
- unresolved data-loss risks classified and addressed or explicitly excluded.

## Prioritization principles

1. Prevent silent corruption before adding convenience.
2. Preserve deterministic automation contracts.
3. Prefer user-reported cases over speculative format breadth.
4. Keep runtime dependencies minimal.
5. Make unsupported behavior explicit.

Feature requests and adoption reports are welcome through the repository issue forms.
