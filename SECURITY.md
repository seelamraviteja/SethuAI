# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security vulnerabilities. Instead,
report them privately via GitHub's
[security advisories](https://github.com/seelamraviteja/SethuAI/security/advisories/new)
or by email to the maintainer. You'll get an acknowledgement as soon as
possible, and we'll coordinate a fix and disclosure timeline with you.

## Hardening notes

SethuAI is **open by default in dev** and **secured via environment variables**
in production. For any deployment reachable beyond localhost, set all three:

- `SETHU_SECRET_KEY` — encryption key for secrets at rest.
- `SETHU_ADMIN_TOKEN` — gates the management API / UI.
- `SETHU_MCP_TOKEN` — gates the hosted MCP endpoint.

When `SETHU_MCP_TOKEN` is set, outbound SSRF protection is enabled automatically
(proxied requests to private/loopback/link-local addresses are refused). You can
force it on or off with `SETHU_BLOCK_PRIVATE_HOSTS=1|0`.
