# NIS2 Netherlands Registration MCP

> ## 🧱 Part of the MEOK Governance Substrate (£499/mo)
> See [meok.ai/governance](https://meok.ai/governance).

# Wbni-2 (NL NIS2) registration packet generator — deadline June 2026

<!-- mcp-name: io.github.CSOAI-ORG/meok-nis2-nl-register-mcp -->

[![PyPI](https://img.shields.io/pypi/v/meok-nis2-nl-register-mcp)](https://pypi.org/project/meok-nis2-nl-register-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## What this does

Generates NCSC-NL-portal-ready Wbni-2 registration packets. Validates org profile, classifies Annex I (essential) / Annex II (important), generates the regulator payload + management-body attestation, emits a HMAC-signed proof of readiness.

## Why NOW

NL Wbni-2 (NIS2 transposition) requires registration + Article 21 risk-management measures by **30 June 2026**. NCSC-NL + sector regulators (DNB / ACM / ILT / IGJ / NVWA) enforce. Late registration: €100K-€10M + named director liability under Wbni-2 §38a.

Most NL Mittelstand orgs are paying €5K-€20K to consultancies for work that's effectively a 30-minute form. This MCP does the form.

## Tools

| Tool | Purpose |
|---|---|
| `classify_entity(sector, headcount, turnover)` | Annex I vs II vs out-of-scope |
| `generate_registration_packet(...)` | NCSC-NL portal payload + management-body attestation |
| `list_sectors()` | Full Annex I + Annex II sector taxonomy |
| `check_deadline_status()` | Days remaining + status flag |
| `sign_readiness_attestation(entity, kvk, controls)` | HMAC-signed Article 21 board sign-off |

## Sister MCPs

- `meok-nis2-de-register-mcp` — German Mittelstand variant
- `dora-nis2-crosswalk-mcp` — DORA × NIS2 dual-compliance map
- `nis2-compliance-mcp` — core Article 21 + Article 23 + Article 20 audit
- `agent-incident-relay-mcp` — Article 23 incident 5-clock broadcaster

Full catalogue: [meok.ai/anthropic-registry](https://meok.ai/anthropic-registry)

## Pricing

| Option | Price |
|---|---|
| Self-host MIT | £0 |
| One-off readiness packet | £499 |
| £99/mo ongoing monitoring | £99/mo |
| Governance Substrate | £499/mo |
| Defence | £4,990/mo |

Buy: https://meok.ai/governance

## Licence

MIT. By [MEOK AI Labs](https://meok.ai) (CSOAI LTD, UK Companies House 16939677).
