# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| < 0.5   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in AIOS, please report it responsibly:

1. **Do NOT** open a public issue
2. Email: *(to be added)* or use [GitHub Security Advisories](https://github.com/yangfei222666-9/aios/security/advisories/new)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Best Practices

When using AIOS:

- **Never commit secrets** to events.jsonl or config files
- **Use environment variables** for API keys and credentials
- **Restrict file permissions** on sensitive data files
- **Review playbooks** before enabling auto-remediation
- **Monitor alert logs** for suspicious activity
- **Keep dependencies updated** (`pip install --upgrade aios-framework`)

## Known Security Considerations

- **Event logs** may contain sensitive data — ensure proper access controls
- **Playbook execution** runs with the same permissions as AIOS — review carefully
- **Dashboard** (port 9091) should not be exposed to the internet without authentication
- **Agent spawning** can consume resources — set appropriate limits

## Disclosure Policy

- We will acknowledge your report within 48 hours
- We will provide a fix timeline within 7 days
- We will credit you in the security advisory (unless you prefer anonymity)
- We will publish a security advisory after the fix is released

## Contact

For security concerns: *(to be added)*

For general questions: [GitHub Discussions](https://github.com/yangfei222666-9/aios/discussions)
