[![MCP Scorecard: 90/100](https://img.shields.io/badge/proofof.ai-90%2F100-5b21b6)](https://proofof.ai/scorecard/meok-nis2-de-register-mcp.html)

# meok-nis2-de-register-mcp

[![PyPI](https://img.shields.io/pypi/v/meok-nis2-de-register-mcp)](https://pypi.org/project/meok-nis2-de-register-mcp/) [![Python](https://img.shields.io/pypi/pyversions/meok-nis2-de-register-mcp)](https://pypi.org/project/meok-nis2-de-register-mcp/)


**BSI-portal-ready NIS2 registration packets for German Mittelstand orgs.**

The NIS2-Umsetzungsgesetz (German NIS2 transposition) took force **6 December 2025**. The BSI registration portal opened **6 January 2026**. ~30,000 in-scope orgs have a **~3-month window** to register — deadline mid-April to early-May 2026. Late registration = up to €2M fines under §38b BSIG, plus personal liability of management body.

By [MEOK AI Labs](https://meok.ai).

## Why this MCP

Most Mittelstand orgs are paying €5K–€20K to consultancies for what is, mechanically, a 30-minute form. This MCP:

1. Validates whether your org is in scope (essential vs important entity, KMU exemption check)
2. Generates the BSI-portal-ready registration packet with all 7 obligation acknowledgements
3. Walks you through Mein Unternehmenskonto submission step-by-step
4. Emits a HMAC-SHA256 signed proof of registration readiness for your audit trail / customer due-diligence requests

## Tools

- `validate_org_profile` — in-scope check + entity type + size class
- `generate_bsi_packet` — full registration JSON (Pro)
- `submit_to_mein_unternehmenskonto` — click-by-click portal walkthrough
- `signed_registration_proof` — Pro: cryptographic proof of completion

## Install

```bash
pip install meok-nis2-de-register-mcp
```

## Tiers

- **Free** — in-scope validation + walkthrough
- **£499 one-off** — full BSI packet generation + signed proof — [buy now](https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t)
- **Pro £199/mo** — unlimited regenerations + monthly compliance refresh + Slack alerts on BSIG amendments — [subscribe](https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t)

Use code **`MEOKEAT`** at checkout for 25% off the first 3 months.

## Sources

- BSIG (NIS2-Umsetzungsgesetz) — https://www.gesetze-im-internet.de/bsig_2009/
- BSI portal — https://www.bsi.bund.de/DE/Themen/Regulierte-Wirtschaft/NIS-2-Umsetzungsgesetz
- Mein Unternehmenskonto — https://mein-unternehmenskonto.de

## Disclaimer

Automated assistance for regulatory preparation. Does not substitute for qualified German legal counsel or BSI's binding determination. MEOK AI Labs provides no warranty of regulatory correctness.

## Full Compliance Platform

NIS2 is just one regulation. **[councilof.ai](https://councilof.ai)** covers EU AI Act, DORA, NIS2, CRA, CSRD compliance from £29/mo.

→ **[Get started at councilof.ai](https://councilof.ai)**

## Related MEOK MCPs

- [`nis2-compliance-mcp`](https://pypi.org/project/nis2-compliance-mcp/) — full NIS2 audit (all 27 EU Member States)
- [`dora-nis2-crosswalk-mcp`](https://pypi.org/project/dora-nis2-crosswalk-mcp/) — banks in scope for both
- [`ai-incident-reporting-mcp`](https://pypi.org/project/ai-incident-reporting-mcp/) — multi-regime incident clocks

## License

MIT — [MEOK AI Labs](https://meok.ai), 2026.

<!-- mcp-name: io.github.CSOAI-ORG/meok-nis2-de-register-mcp -->

<!-- meok-moat-footer-v1 -->
---

## Pairs with MEOK Governance Suite

Build something that touches users? You need compliance. MEOK ships 38 governance MCPs that drop in alongside this tool — EU AI Act, DORA, NIS2, CRA, GDPR, ISO 42001, FDA SaMD, MDR, Basel, MiFID II, MiCA, COPPA, and more.

```bash
# One-shot install of the governance pack
npx meok-setup --pack governance
```

Free tier: 10 calls/day per MCP. Pro tier (£79/mo): unlimited + cryptographically signed compliance attestations your auditor verifies independently.

→ Full catalogue: [councilof.ai/catalogue](https://councilof.ai/catalogue)
→ MEOK AI Labs: [meok.ai](https://meok.ai)

<!-- BUY-LADDER:START -->

## 💸 Try MEOK in 30 seconds — instant buy ladder

| Tier | Price | What you get | Stripe |
|---|---|---|---|
| Smoke test | **£1** | Signed sample MCP-Hardening report + Article 50 PDF | <https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t> |
| Quick Kit | **£9** | EU AI Act Article 50 implementation guide (C2PA + EU-Icon) | <https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t> |
| Founder Call | **£29** | 30-min 1-on-1 with the founder | <https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t> |

> Refundable. UK Stripe — VAT-clean. Builds on the 81-MCP MEOK fleet.
> Verify any signed report at <https://meok.ai/verify>.

<!-- BUY-LADDER:END -->



## Configuration

Add to your `claude_desktop_config.json` (Claude Desktop) or your MCP client config:

```json
{
  "mcpServers": {
    "meok-nis2-de-register-mcp": {
      "command": "uvx",
      "args": ["meok-nis2-de-register-mcp"]
    }
  }
}
```

Or: `pip install meok-nis2-de-register-mcp` then run the `meok-nis2-de-register-mcp` command (stdio transport).

## Examples

Once configured, ask your assistant, for example:
- "Use `validate_org_profile` to …"
- "Use `generate_bsi_packet` to …"
- "Use `submit_to_mein_unternehmenskonto` to …"
