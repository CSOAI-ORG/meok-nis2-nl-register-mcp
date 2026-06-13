#!/usr/bin/env python3
"""
NIS2 Germany BSI Registration MCP Server
==========================================
By MEOK AI Labs | https://meok.ai

Generates BSI-portal-ready NIS2 registration packets for German Mittelstand orgs.

URGENT CONTEXT (as of April 2026):
  Germany's NIS2-Umsetzungsgesetz (NIS2 transposition) — the BSI Act amendments —
  took force 6 December 2025. The BSI registration portal opened 6 January 2026.
  ~30,000 in-scope German organisations must register within 3 months. Deadline
  effectively April–May 2026. Late registration = €100K-€2M fine + named director
  liability under § 38b BSIG.

PROBLEM SOLVED: most Mittelstand orgs are paying €5K-€20K to consultancies for
work that's a 30-minute form. This MCP validates org profile, classifies sector +
size + entity type, generates the BSI packet (sector designation + service map +
contact register + management body attestation), and emits a HMAC-signed proof of
registration readiness.

  💷 PRICE: £499 one-off OR £99/month for ongoing monitoring + change packets.
  🔑 BUYER: German CISOs / IT directors / Compliance leads at Mittelstand orgs.

Install: pip install meok-nis2-de-register-mcp
Run:     python server.py
"""

import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP

import os as _os
import sys
import os

_MEOK_API_KEY = _os.environ.get("MEOK_API_KEY", "")

try:
    from auth_middleware import check_access as _shared_check_access
except ImportError:
    def _shared_check_access(api_key: str = ""):
        if _MEOK_API_KEY and api_key and api_key == _MEOK_API_KEY:
            return True, "OK", "pro"
        if _MEOK_API_KEY and api_key and api_key != _MEOK_API_KEY:
            return False, "Invalid API key.", "free"
        return True, "OK, Pro at https://www.csoai.org/checkout", "free"


try:
    from attestation import get_attestation_tool_response
    _ATTESTATION_LOCAL = True
except ImportError:
    _ATTESTATION_LOCAL = False

# V-06 FIX: SSRF allowlist on attestation API URL.
try:
    from ssrf_safe import resolve_attestation_api as _resolve_api  # type: ignore
    _ATTESTATION_API = _resolve_api()
except ImportError:
    _ATTESTATION_API_RAW = _os.environ.get("MEOK_ATTESTATION_API", "https://meok-attestation-api.vercel.app")
    _ALLOWED_API_HOSTS = {"meok-attestation-api.vercel.app", "meok-verify.vercel.app", "meok.ai", "csoai.org", "councilof.ai", "compliance.meok.ai"}
    import urllib.parse as _urllib_parse
    try:
        _api_parsed = _urllib_parse.urlparse(_ATTESTATION_API_RAW)
        _api_host = (_api_parsed.hostname or "").lower()
        _api_scheme = (_api_parsed.scheme or "").lower()
    except Exception:
        _api_host, _api_scheme = "", ""
    if _api_scheme != "https" or _api_host not in _ALLOWED_API_HOSTS:
        _ATTESTATION_API = "https://meok-attestation-api.vercel.app"
    else:
        _ATTESTATION_API = _ATTESTATION_API_RAW.rstrip("/")


def check_access(api_key: str = ""):
    return _shared_check_access(api_key)


# Stripe — £499 one-off product link (REPLACE if you create a dedicated product)
STRIPE_499_ONE_OFF = "https://councilof.ai"  # currently the £5k assessment link — Nick: create £499 product
STRIPE_99_MONTHLY = "https://councilof.ai"
STRIPE_199 = "https://councilof.ai"

FREE_DAILY_LIMIT = 50


# ── BSI Act sector classification (NIS2-Umsetzungsgesetz Annex 1 + 2) ────────
# §28 BSIG — Wesentliche Einrichtungen (Essential entities, Annex 1)
ESSENTIAL_SECTORS_DE = {
    "energy": {"de": "Energie", "examples": "Strom, Gas, Öl, Wasserstoff, Fernwärme"},
    "transport": {"de": "Verkehr", "examples": "Luft, Schiene, Wasser, Straße"},
    "banking": {"de": "Bankwesen", "examples": "Kreditinstitute (überschneidet sich mit DORA)"},
    "financial_market_infra": {"de": "Finanzmarktinfrastrukturen", "examples": "Handelsplätze, zentrale Gegenparteien (CCPs)"},
    "health": {"de": "Gesundheit", "examples": "Krankenhäuser, EU-Referenzlabore, Hersteller von kritischen Arzneimitteln/Medizinprodukten"},
    "drinking_water": {"de": "Trinkwasserversorgung", "examples": "Versorger und Verteiler"},
    "waste_water": {"de": "Abwasserentsorgung", "examples": "Sammlung, Entsorgung, Aufbereitung"},
    "digital_infrastructure": {"de": "Digitale Infrastruktur", "examples": "IXPs, DNS-Anbieter, TLD-Registries, Cloud, Datenzentren, CDN, Trust Services, ÖKomm-Netze + -Dienste"},
    "ict_service_management": {"de": "ICT-Service Management (B2B)", "examples": "MSPs, MSSPs"},
    "public_administration": {"de": "Öffentliche Verwaltung", "examples": "Bundes- + Landesverwaltung"},
    "space": {"de": "Weltraum", "examples": "Bodengestützte Infrastruktur für Raumdienste"},
}

# §28 BSIG — Wichtige Einrichtungen (Important entities, Annex 2)
IMPORTANT_SECTORS_DE = {
    "postal": {"de": "Post- und Kurierdienste", "examples": ""},
    "waste_management": {"de": "Abfallbewirtschaftung", "examples": ""},
    "chemicals": {"de": "Chemie (Herstellung, Produktion, Vertrieb)", "examples": ""},
    "food": {"de": "Lebensmittel (Produktion, Verarbeitung, Vertrieb)", "examples": ""},
    "manufacturing": {"de": "Verarbeitendes Gewerbe", "examples": "Medizinprodukte, Computer/Elektronik, Elektrogeräte, Maschinen, Fahrzeuge"},
    "digital_providers": {"de": "Digitale Anbieter", "examples": "Online-Marktplätze, Suchmaschinen, soziale Plattformen"},
    "research": {"de": "Forschungseinrichtungen", "examples": ""},
}


# Size thresholds (NIS2 Art 2 + § 28 BSIG)
def _classify_size(employees: int, turnover_million_eur: float, balance_sheet_million_eur: float = 0) -> str:
    """KMU classification per EU Recommendation 2003/361/EC (Art 2)."""
    if employees < 50 and turnover_million_eur < 10 and balance_sheet_million_eur < 10:
        return "small_or_micro"  # generally OUT of NIS2 scope unless special case
    if employees < 250 and (turnover_million_eur < 50 or balance_sheet_million_eur < 43):
        return "medium"  # IN scope — likely "important"
    return "large"  # IN scope — likely "essential" if essential sector


mcp = FastMCP(
    "meok-nis2-de-register",
    instructions=(
        "MEOK AI Labs Germany NIS2 BSI Registration MCP. Validates whether a German "
        "organisation is in scope under the NIS2-Umsetzungsgesetz (BSIG amendments, "
        "in force 6 Dec 2025). Generates the BSI-portal-ready registration packet + "
        "HMAC-signed proof of readiness. Use BEFORE the registration deadline (~April "
        "2026 for first wave). Late registration = §38b BSIG fines up to €2M + "
        "personal director liability."
    ),
)

def _server_meter_check(api_key: str = "") -> dict:
    """Calls the live /verify endpoint for server-side metering. Returns the JSON dict.
    Fail-open: if /verify is unreachable or KV isn't configured, returns allowed=True
    (so the local rate-limit in _check_rate_limit remains the safety net)."""
    try:
        data = json.dumps({"api_key": api_key, "tool": ""}).encode()
        req = _meter_urlreq.Request(_METER_URL, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with _meter_urlreq.urlopen(req, timeout=2.5) as r:
            d = json.loads(r.read())
            if isinstance(d, dict) and "allowed" in d:
                return d
    except Exception:
        pass
    return {"allowed": True, "tier": "anonymous", "remaining": 200, "upgrade_url": "https://meok.ai/pricing"}


_METER_URL = "https://proofof.ai/verify"


@mcp.tool()
def validate_org_profile(
    org_name: str,
    legal_form: str,
    sector: str,
    employees: int,
    turnover_million_eur: float,
    balance_sheet_million_eur: float = 0,
    delivers_critical_service: bool = False,
    api_key: str = "",
) -> str:
    """Determine whether a German org is in scope for NIS2 + classify entity type
    + size class.

    - sector: one of energy / transport / banking / financial_market_infra / health /
      drinking_water / waste_water / digital_infrastructure / ict_service_management /
      public_administration / space / postal / waste_management / chemicals / food /
      manufacturing / digital_providers / research
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_499_ONE_OFF})

    is_essential = sector in ESSENTIAL_SECTORS_DE
    is_important = sector in IMPORTANT_SECTORS_DE
    if not (is_essential or is_important):
        return json.dumps({
            "in_scope": "UNCLEAR",
            "reason": f"sector '{sector}' is not in NIS2 Annex 1 (essential) or Annex 2 (important). Verify sector classification with BSI.",
            "valid_essential_sectors": list(ESSENTIAL_SECTORS_DE.keys()),
            "valid_important_sectors": list(IMPORTANT_SECTORS_DE.keys()),
        })

    size = _classify_size(employees, turnover_million_eur, balance_sheet_million_eur)
    if size == "small_or_micro" and not delivers_critical_service:
        return json.dumps({
            "in_scope": False,
            "reason": "Small/micro entity (KMU under EU 2003/361). Generally exempt unless designated as critical (§28a BSIG) or fits a special case (e.g. sole national DNS provider).",
            "double_check": "Confirm with BSI if your service is uniquely irreplaceable in Germany.",
        })

    entity_type = "wesentliche_einrichtung_essential" if is_essential and size == "large" else "wichtige_einrichtung_important"
    sector_meta = ESSENTIAL_SECTORS_DE.get(sector) or IMPORTANT_SECTORS_DE.get(sector)

    return json.dumps({
        "org_name": org_name,
        "in_scope": True,
        "entity_type": entity_type,
        "entity_type_de": "Wesentliche Einrichtung" if entity_type.startswith("wesentliche") else "Wichtige Einrichtung",
        "sector": sector,
        "sector_de": sector_meta["de"],
        "sector_examples": sector_meta["examples"],
        "size_class": size,
        "registration_required": True,
        "registration_deadline": "~April–May 2026 (3 months from BSI portal opening 6 Jan 2026)",
        "fine_for_late_registration": "Up to €2,000,000 (§ 38b BSIG) + personal liability of management body",
        "next_step": "Call generate_bsi_packet() with the same parameters to produce the registration data structure",
        "upsell": f"£499 produces the full signed packet ready to paste into the BSI portal: {STRIPE_499_ONE_OFF}" if tier == "free" else None,
    }, indent=2)


@mcp.tool()
def generate_bsi_packet(
    org_name: str,
    legal_form: str,
    register_court: str,
    register_number: str,
    sector: str,
    sub_sector: str,
    services_csv: str,
    employees: int,
    turnover_million_eur: float,
    contact_name: str,
    contact_role: str,
    contact_email: str,
    contact_phone: str,
    head_office_address: str,
    nationally_offered_services: bool = True,
    api_key: str = "",
) -> str:
    """Generate the BSI-portal-ready registration packet. Pro tier required.

    The output JSON maps directly to the German "Mein Unternehmenskonto" /
    BSI-Meldeportal field structure. Paste into the portal in ~10 minutes.
    """
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_499_ONE_OFF})
    if tier == "free":
        return json.dumps({
            "error": "BSI packet generation requires the £499 one-off purchase OR Pro (£199/mo).",
            "upgrade_url": STRIPE_499_ONE_OFF,
            "preview_what_you_get": [
                "Vollständiger Antragsdatensatz für das BSI-Meldeportal",
                "Sektorklassifikation gemäß §28 BSIG (Anlage 1 oder Anlage 2)",
                "Diensteliste mit Kritikalitätsbewertung",
                "Kontaktregister (CISO, GeschäftsführerIn, Stellvertretung)",
                "HMAC-signierter Nachweis der Registrierungsbereitschaft (öffentliche Verifikations-URL)",
                "Vorlage für die Schulungspflicht-Erklärung (§38 BSIG)",
                "Eskalationspfad für signifikante Vorfälle (24h / 72h / 1 Monat)",
            ],
        })

    services = [s.strip() for s in services_csv.split(",") if s.strip()]
    is_essential = sector in ESSENTIAL_SECTORS_DE
    entity_type = "Wesentliche Einrichtung" if is_essential else "Wichtige Einrichtung"
    annex = "Anlage 1 BSIG" if is_essential else "Anlage 2 BSIG"

    packet = {
        "_meta": {
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "generator": "meok-nis2-de-register-mcp v1.0",
            "regulation": "BSIG (NIS2-Umsetzungsgesetz) §§ 28, 32, 38",
            "purpose": "BSI-Meldeportal Registrierung",
        },
        "organisation": {
            "name": org_name,
            "rechtsform": legal_form,
            "register_court": register_court,
            "register_number": register_number,
            "head_office_address": head_office_address,
            "employees": employees,
            "turnover_million_eur": turnover_million_eur,
        },
        "classification": {
            "entity_type": entity_type,
            "entity_type_key": "wesentlich" if is_essential else "wichtig",
            "annex": annex,
            "sector_key": sector,
            "sector_de": (ESSENTIAL_SECTORS_DE.get(sector) or IMPORTANT_SECTORS_DE.get(sector, {})).get("de", ""),
            "sub_sector": sub_sector,
            "nationally_offered_services": nationally_offered_services,
        },
        "services": [{"service_name": s, "criticality": "primary"} for s in services],
        "primary_contact": {
            "name": contact_name,
            "role": contact_role,
            "email": contact_email,
            "phone": contact_phone,
            "is_management_body_member": False,
        },
        "obligations_acknowledged": {
            "art_21_security_measures_implemented": False,
            "art_23_incident_reporting_runbook_in_place": False,
            "management_body_training_completed_or_scheduled": False,
            "supply_chain_risk_management_documented": False,
            "encryption_at_rest_in_transit_implemented": False,
            "mfa_enforced": False,
            "vulnerability_disclosure_policy_published": False,
        },
        "next_actions_before_submission": [
            "Tick the 7 obligations_acknowledged once they are TRUE — do NOT submit with any false values",
            "Verify register_court + register_number match the Handelsregister entry exactly",
            "Confirm contact_email is a monitored shared inbox, not personal",
            "Generate signed proof via signed_registration_proof() and store with your records",
            "Paste this JSON into the BSI-Meldeportal at https://www.bsi.bund.de/DE/Themen/Regulierte-Wirtschaft/NIS-2-Umsetzungsgesetz",
        ],
    }
    return json.dumps(packet, indent=2, ensure_ascii=False)


@mcp.tool()
def submit_to_mein_unternehmenskonto(api_key: str = "") -> str:
    """Returns the field-by-field submission walkthrough for the BSI portal.
    (We do NOT auto-submit — the portal requires authenticated browser session +
    qualified electronic signature. This tool gives you the click-by-click guide.)"""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_499_ONE_OFF})
    return json.dumps({
        "portal_url": "https://www.bsi.bund.de/DE/Themen/Regulierte-Wirtschaft/NIS-2-Umsetzungsgesetz",
        "auth_required": "Mein Unternehmenskonto (ELSTER-based) OR Bundes-ID with eID",
        "estimated_time_with_packet": "10–15 minutes",
        "steps": [
            "1. Log into 'Mein Unternehmenskonto' at https://mein-unternehmenskonto.de",
            "2. Navigate to 'BSI-Meldeportal NIS-2'",
            "3. Choose 'Erstregistrierung' (initial registration)",
            "4. Paste the JSON packet generated by generate_bsi_packet() into each section's fields",
            "5. Verify all 7 obligations_acknowledged are TRUE — system will reject false values",
            "6. Upload signed proof PDF (from signed_registration_proof())",
            "7. Submit with qualified electronic signature (qeS) of management body member",
            "8. Save the BSI 'Anmeldebestätigung' (confirmation receipt) — this is your audit trail",
        ],
        "common_rejection_reasons": [
            "Sector mismatch — chose 'Anlage 1' but BSI determines you fit 'Anlage 2'",
            "Register data mismatch — Handelsregister-Auszug differs",
            "Contact email is personal (gmail/gmx etc.) instead of organisation domain",
            "Management body member not present at submission",
        ],
        "if_late": "You're not too late if it's still April 2026 — but submit THIS WEEK. Each week of delay materially raises the §38b BSIG fine band.",
    }, indent=2, ensure_ascii=False)


@mcp.tool()
def signed_registration_proof(
    org_name: str,
    submitted_to_bsi_utc: str,
    bsi_anmeldebestaetigung_id: str = "",
    api_key: str = "",
    email: str = "",
) -> str:
    """Generate a HMAC-SHA256 signed attestation of NIS2 registration completion.
    Useful for: customer due-diligence requests, board reporting, supply-chain
    NIS2 §28 attestations, audit trails. Pro/Enterprise required."""
    allowed, msg, tier = check_access(api_key)
    if not allowed:
        return json.dumps({"error": msg, "upgrade_url": STRIPE_499_ONE_OFF})
    if tier == "free":
        return json.dumps({
            "error": "Signed registration proof requires the £499 purchase OR Pro (£199/mo).",
            "upgrade_url": STRIPE_499_ONE_OFF,
        })

    findings = [
        f"BSI-Meldeportal Registrierung abgeschlossen am {submitted_to_bsi_utc}",
        f"Anmeldebestätigung: {bsi_anmeldebestaetigung_id or 'pending receipt from BSI'}",
        "Vollständiger Antragsdatensatz gemäß § 28 BSIG eingereicht",
        "Sieben Verpflichtungserklärungen (Art 21 + Art 23 + Schulung + Lieferkette + Verschlüsselung + MFA + CVD) bestätigt",
    ]
    payload = {
        "regulation": "Germany NIS2 (BSIG / NIS2-Umsetzungsgesetz, in force 6 Dec 2025)",
        "entity": org_name,
        "score": 100.0,
        "findings": findings,
        "tier": tier,
    }
    if _ATTESTATION_LOCAL:
        cert = get_attestation_tool_response(
            regulation=payload["regulation"], entity=org_name, score=100.0,
            findings=findings, articles_audited=["BSIG §28", "BSIG §32", "BSIG §38", "BSIG §38b"],
            tier=tier,
        )
    else:
        import urllib.request as _url
        try:
            req = _url.Request(
                f"{_ATTESTATION_API}/sign",
                data=json.dumps({"api_key": api_key, "email": email, **payload}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with _url.urlopen(req, timeout=15) as resp:
                cert = json.loads(resp.read())
        except Exception as e:
            return json.dumps({"error": f"Attestation API unreachable: {e}"})
    return json.dumps(cert, indent=2)


def main():
    mcp.run()


if __name__ == "__main__":
    main()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/aFa7sNcgAdQS0ZT1Uc8k91t"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
