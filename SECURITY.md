# Security Policy

Codex-teammode Workflow ships **prompts and documentation**, not executable services. Traditional CVE-style vulnerabilities are unlikely.

That said, please report the following privately:

- **Prompt-injection patterns** that could cause an installing agent to bypass safety rules, for example blindly overwriting target files, exfiltrating secrets, or ignoring the `Hard Rules` section of `BOOTSTRAP_PROMPT.md`.
- **Leaked secrets or PII** found anywhere in this repo.
- **License or attribution issues**.

## How to report

Email: `19922108279@163.com`

Please do not open a public issue for the above.

## What to expect

- Acknowledgement within 7 days.
- A fix or mitigation plan within 30 days where applicable.

## Out of scope

- Bugs in third-party AI agents such as Codex or Claude Code. Report those to the vendor.
- General disagreement with workflow choices — please open a regular issue or discussion instead.
