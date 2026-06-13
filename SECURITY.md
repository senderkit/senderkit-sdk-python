# Security Policy

## Reporting a vulnerability

Please **do not** report security vulnerabilities through public GitHub issues.

Instead, report them privately via GitHub's
[security advisory form](https://github.com/senderkit/senderkit-sdk-python/security/advisories/new),
or email **security@senderkit.com**.

Please include:

- A description of the vulnerability and its impact.
- Steps to reproduce or a proof of concept.
- The SDK version and Python version affected.

We aim to acknowledge reports within 3 business days and to provide a remediation
timeline after triage. We will credit reporters in the release notes unless you
prefer to remain anonymous.

## Supported versions

Security fixes are released for the latest minor version. We recommend always
running the most recent release.

## Handling credentials

The SDK never logs API keys or webhook signing secrets. When filing bug reports
or sharing tracebacks, redact any `sk_...` API keys and signing secrets.
