# Security Policy – LaViPoP

**LaViPoP – Language-aware Video Post-Processing**

Copyright © 2026 TopLab – Toplak Laboratory e.U., Austria.

## 1. Security Commitment

LaViPoP is an open-source video post-processing application developed and maintained by TopLab – Toplak Laboratory e.U.

We aim to develop and maintain LaViPoP according to established secure software development practices, with particular attention to:

- Secure processing of video and multimedia files.
- Protection against malformed or malicious media inputs.
- Secure handling of local files, directories, and configuration data.
- Security of Python dependencies, FFmpeg, and third-party libraries.
- Secure deployment in local, containerized, and on-premise environments.
- Responsible vulnerability management and coordinated disclosure.

Security is considered throughout development, testing, and maintenance.

## 2. Supported Versions

Security maintenance is provided for the latest official stable release of LaViPoP, subject to the project's published maintenance commitments.

| Version | Security Support |
|---|---|
| Latest stable release | Supported |
| Previous releases | Not routinely supported |
| Development / experimental builds | Not supported |

Users should keep their installations updated and review published security advisories.

Commercial editions may have separate contractual maintenance and support terms.

## 3. Reporting a Vulnerability

If you discover a potential security vulnerability, please report it privately.

**Preferred reporting method:**

Use GitHub's **Report a vulnerability** feature in the Security tab of the official LaViPoP repository, if enabled.

Do not disclose exploitable security vulnerabilities through public GitHub Issues, Discussions, or other public channels before coordinated disclosure.

A useful report should include:

- A description of the vulnerability and its potential impact.
- The affected LaViPoP version.
- Relevant operating system and deployment information.
- Steps to reproduce the issue.
- A minimal proof of concept, where appropriate.
- Relevant logs or error messages with sensitive information removed.

Please do not include passwords, authentication tokens, customer data, or other confidential information in reports.

## 4. Vulnerability Handling

TopLab will review privately submitted vulnerability reports and assess their reproducibility, severity, and potential impact.

The intended process is:

1. Receive and review the report.
2. Assess whether the reported issue is a security vulnerability.
3. Investigate affected components and supported versions.
4. Develop and test a corrective measure.
5. Publish an appropriate security update or mitigation.
6. Coordinate public disclosure where appropriate.

We aim to acknowledge reports within five business days, where reasonably possible.

Resolution times depend on the severity, technical complexity, and availability of a suitable correction. No universal remediation deadline or guaranteed response time is implied for the Community Edition.

Confirmed vulnerabilities may be documented through GitHub Security Advisories and, where appropriate, assigned a CVE identifier.

## 5. Coordinated Disclosure

We encourage responsible and coordinated vulnerability disclosure.

Reporters are requested to:

- Allow reasonable time for investigation and remediation before public disclosure.
- Avoid accessing, modifying, or disclosing information belonging to others.
- Avoid activities that degrade service availability or compromise third-party systems.
- Conduct testing only on systems and data they own or are explicitly authorized to test.

Publication of technical details should preferably be coordinated with TopLab to reduce risks to affected users.

This policy does not establish a public bug bounty program or authorize testing of systems operated by TopLab or third parties.

## 6. External Contributions

LaViPoP development and the official source code repository are maintained exclusively by TopLab.

External source code contributions and pull requests are not currently accepted.

However, security researchers and users are encouraged to submit vulnerability reports, reproduction instructions, and mitigation suggestions through the private reporting process.

Security fixes for official releases are developed, reviewed, and integrated by TopLab.

This policy does not restrict the rights granted by the Apache License 2.0.

## 7. Security Considerations for Deployment

LaViPoP processes multimedia files that may originate from untrusted sources.

Users and system administrators should:

- Install only official releases or builds from trusted sources.
- Keep the operating system, Python runtime, FFmpeg, and dependencies updated.
- Run LaViPoP with the minimum necessary operating-system privileges.
- Restrict access to directories containing confidential video files.
- Avoid exposing local development instances directly to the public internet.
- Restrict network access to processing services unless explicitly required.
- Protect configuration files, credentials, and processing logs.
- Perform regular backups where operationally necessary.

Docker and on-premise installations should follow the principle of least privilege and apply suitable resource and network restrictions.

## 8. Data Protection and Privacy

LaViPoP is designed to support local and on-premise video post-processing.

When deployed locally without optional online integrations, video-processing data can remain within the user's own infrastructure.

Users and operators remain responsible for configuring appropriate storage permissions, backup procedures, access controls, and retention policies.

Any future cloud-hosted edition will be governed by separate privacy and security documentation.

## 9. Third-Party Dependencies

LaViPoP relies on third-party software, including Python libraries and FFmpeg.

Vulnerabilities in these components may affect LaViPoP installations.

TopLab intends to monitor relevant dependency security advisories and evaluate necessary updates for supported releases.

Users are encouraged to report suspected vulnerabilities involving dependencies when these may affect LaViPoP.

## 10. Security Updates

Security updates and relevant advisories will be communicated through the official GitHub repository and its release mechanisms.

Users are encouraged to monitor:

- GitHub Releases
- GitHub Security Advisories
- Official LaViPoP project documentation

For commercial deployments, separate maintenance, update, and support arrangements may apply.

## 11. Disclaimer

LaViPoP Community Edition is provided under the Apache License, Version 2.0, including its applicable warranty and liability provisions.

This security policy describes the project's vulnerability reporting and maintenance practices. It does not create additional contractual service-level guarantees.

Applicable statutory obligations and any separate commercial agreements remain unaffected.

---

**Maintainer:** TopLab – Toplak Laboratory e.U., Austria

**Project:** LaViPoP – Language-aware Video Post-Processing

**License:** Apache License 2.0

**Website:** https://www.toplab.at/
