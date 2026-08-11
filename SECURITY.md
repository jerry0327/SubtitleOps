# Security policy

## Supported versions

SubtitleOps is currently pre-1.0. Security fixes are applied to the latest release and the `main` branch.

## Reporting a vulnerability

Please do **not** publish exploit details in a public GitHub issue.

Use GitHub's private vulnerability reporting feature for this repository when available. Include:

- affected version/commit;
- a minimal reproducer;
- expected impact;
- any suggested mitigation.

Subtitle files are untrusted input. Reports involving denial of service, parser crashes on bounded input, path handling, or unsafe output behavior are in scope. Subtitle content that merely renders incorrectly without a security consequence is better filed as a normal bug.
