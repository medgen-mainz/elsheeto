# Security Policy

## Supported versions

Only the latest released version of `elsheeto` receives security fixes.

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

Report it privately through GitHub's
[private vulnerability reporting](https://github.com/medgen-mainz/elsheeto/security/advisories/new),
or by email to <manuel.holtgrewe@medgen-mainz.de>.

Please include a description of the issue, the affected version, and steps to
reproduce it. You can expect an acknowledgement within 14 days.

## Scope

`elsheeto` parses sample sheet files. Treat sample sheets from untrusted sources as
untrusted input: reports of crashes, unbounded resource consumption, or any escape
from pure parsing behaviour triggered by a malformed file are in scope.

## Release integrity

Releases are published to PyPI from GitHub Actions using
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/), and are signed with
[PEP 740](https://peps.python.org/pep-0740/) attestations. No long-lived API token
exists that could be used to publish this package.
