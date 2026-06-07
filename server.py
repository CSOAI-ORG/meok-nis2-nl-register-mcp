#!/usr/bin/env python3
"""
Buy Pro: https://www.csoai.org/checkout

NIS2 Netherlands Registration MCP
==================================

By MEOK AI Labs · https://meok.ai · MIT
<!-- mcp-name: io.github.CSOAI-ORG/meok-nis2-nl-register-mcp -->

URGENT CONTEXT (May 2026)
-------------------------
Netherlands NIS2 transposition (Wbni-2) entered force in Q1 2026 after a delay.
The NL competent authority is NCSC-NL + sector-specific regulators (DNB for
finance, ACM for telco, ILT for transport, IGJ for health). Self-assessment +
registration is **due June 2026** for essential + important entities under
Annex I and Annex II.

This MCP validates an org profile, classifies entity type (essential vs
important + sector), generates the NCSC-NL portal payload + management-body
attestation, and emits a HMAC-signed proof of registration readiness.

Companion to:
- `meok-nis2-de-register-mcp` (the German Mittelstand variant)
- `dora-nis2-crosswalk-mcp` (DORA × NIS2 dual-compliance mapping)

PRICE: £499 one-off · £99/mo ongoing monitoring · Substrate £499/mo.
"""

from __future__ import annotations
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("meok-nis2-nl-register")
_HMAC_SECRET = os.environ.get("MEOK_HMAC_SECRET", "")


# ──────────────────────────────────────────────────────────────────────
# Wbni-2 (NL NIS2) sector taxonomy
# ──────────────────────────────────────────────────────────────────────

ANNEX_I_ESSENTIAL = {
    "energie":        {"label": "Energy", "regulator": "ACM"},
    "vervoer":        {"label": "Transport", "regulator": "ILT"},
    "bankwezen":      {"label": "Banking", "regulator": "DNB"},
    "financien":      {"label": "Financial market infrastructure", "regulator": "DNB"},
    "gezondheidszorg":{"label": "Health", "regulator": "IGJ"},
    "drinkwater":     {"label": "Drinking water", "regulator": "ILT"},
    "afvalwater":     {"label": "Waste water", "regulator": "ILT"},
    "digitale_infra": {"label": "Digital infrastructure", "regulator": "ACM"},
    "ict_management": {"label": "ICT management (B2B)", "regulator": "NCSC-NL"},
    "publieke_diensten": {"label": "Public administration", "regulator": "NCSC-NL"},
    "ruimte":         {"label": "Space", "regulator": "NCSC-NL"},
}

ANNEX_II_IMPORTANT = {
    "post_koerier":   {"label": "Postal and courier services", "regulator": "ACM"},
    "afval":          {"label": "Waste management", "regulator": "ILT"},
    "chemie":         {"label": "Chemicals", "regulator": "ILT"},
    "voedsel":        {"label": "Food production / processing", "regulator": "NVWA"},
    "industrie":      {"label": "Manufacturing (medical / computer / electrical / motor / transport)", "regulator": "NCSC-NL"},
    "digitale_aanbieders": {"label": "Digital providers (search / cloud / social network / marketplace)", "regulator": "ACM"},
    "onderzoek":      {"label": "Research organisations", "regulator": "NCSC-NL"},
}

REGISTRATION_DEADLINE = "2026-06-30"


def _sign(payload: dict) -> str:
    if not _HMAC_SECRET:
        return "unsigned-no-key-configured"
    return hmac.new(_HMAC_SECRET.encode(), json.dumps(payload, sort_keys=True).encode(), hashlib.sha256).hexdigest()


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


# ──────────────────────────────────────────────────────────────────────
# Tools
# ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def classify_entity(sector: str, headcount: int, annual_turnover_eur: int) -> dict:
    """
    Classify an NL organisation as essential / important / out-of-scope under Wbni-2.

    Args:
        sector: One of the keys in ANNEX_I_ESSENTIAL or ANNEX_II_IMPORTANT.
        headcount: Number of employees.
        annual_turnover_eur: Annual turnover in EUR.

    Returns:
        {scope, classification, sector_label, regulator, size_category}
    """
    sector_key = sector.lower().replace("-", "_").replace(" ", "_")

    # Size category (NIS2 Article 2(1))
    if headcount >= 250 or annual_turnover_eur >= 50_000_000:
        size = "large"
    elif headcount >= 50 or annual_turnover_eur >= 10_000_000:
        size = "medium"
    else:
        size = "small"

    if sector_key in ANNEX_I_ESSENTIAL:
        meta = ANNEX_I_ESSENTIAL[sector_key]
        cls = "essential"
        in_scope = (size in {"large", "medium"})
    elif sector_key in ANNEX_II_IMPORTANT:
        meta = ANNEX_II_IMPORTANT[sector_key]
        cls = "important"
        in_scope = (size in {"large", "medium"})
    else:
        return {
            "scope": "out_of_scope",
            "classification": "n/a",
            "sector_label": "unknown sector",
            "regulator": "n/a",
            "size_category": size,
            "hint": f"Sector key not found. Try one of: {list(ANNEX_I_ESSENTIAL) + list(ANNEX_II_IMPORTANT)}",
        }

    return {
        "scope": "in_scope" if in_scope else "out_of_scope",
        "classification": cls,
        "sector_key": sector_key,
        "sector_label": meta["label"],
        "regulator": meta["regulator"],
        "size_category": size,
        "deadline": REGISTRATION_DEADLINE,
        "hint": "Call generate_registration_packet() with the validated profile." if in_scope else "Below thresholds — no registration required, but voluntary opt-in possible.",
    }


@mcp.tool()
def generate_registration_packet(
    entity_legal_name: str,
    kvk_number: str,
    sector_key: str,
    headcount: int,
    annual_turnover_eur: int,
    primary_contact_email: str,
    management_body_member: str,
    cisos_attestation: bool = False,
    bsn_or_lei: Optional[str] = None,
) -> dict:
    """
    Generate the NCSC-NL registration packet for one entity.

    Args:
        entity_legal_name: Registered name from KvK.
        kvk_number: Dutch Chamber of Commerce number.
        sector_key: From ANNEX_I_ESSENTIAL or ANNEX_II_IMPORTANT.
        headcount: Employees.
        annual_turnover_eur: Annual turnover EUR.
        primary_contact_email: NL security contact.
        management_body_member: Name + role of management-body sign-off (Wbni-2 §10).
        cisos_attestation: Has the CISO attested to risk-management measures?
        bsn_or_lei: Optional BSN / LEI for cross-reference.

    Returns:
        {packet, signature, days_to_deadline}
    """
    classification = classify_entity(sector_key, headcount, annual_turnover_eur)
    today = datetime.now(timezone.utc).date()
    deadline = datetime.fromisoformat(REGISTRATION_DEADLINE).date()
    days_left = (deadline - today).days

    packet = {
        "wbni_2_registration": {
            "entity_legal_name": entity_legal_name,
            "kvk_number": kvk_number,
            "bsn_or_lei": bsn_or_lei,
            "sector_classification": classification,
            "primary_contact": {"email": primary_contact_email},
            "management_body": {
                "named_member": management_body_member,
                "wbni_2_clause": "§10 verantwoordingsplicht (accountability obligation)",
            },
            "cisos_attestation": cisos_attestation,
            "submitted_at": _ts(),
            "deadline": REGISTRATION_DEADLINE,
            "days_to_deadline": days_left,
        }
    }
    packet["signature"] = _sign(packet)
    next_step = ("Submit the packet via the NCSC-NL portal: https://www.ncsc.nl/onderwerpen/nis2"
                 if classification["scope"] == "in_scope"
                 else "Out of scope. No submission required.")
    return {
        "packet": packet,
        "signature": packet["signature"],
        "days_to_deadline": days_left,
        "next_step": next_step,
        "regulator": classification.get("regulator"),
        "post_deadline_risk": "€100K-€10M fine + named director liability (Wbni-2 §38a)" if days_left < 0 else None,
    }


@mcp.tool()
def list_sectors() -> dict:
    """Return the Wbni-2 sector taxonomy — Annex I + Annex II."""
    return {
        "annex_i_essential": ANNEX_I_ESSENTIAL,
        "annex_ii_important": ANNEX_II_IMPORTANT,
        "registration_deadline": REGISTRATION_DEADLINE,
        "total_essential": len(ANNEX_I_ESSENTIAL),
        "total_important": len(ANNEX_II_IMPORTANT),
    }


@mcp.tool()
def check_deadline_status() -> dict:
    """How many days until the Wbni-2 registration deadline?"""
    today = datetime.now(timezone.utc).date()
    deadline = datetime.fromisoformat(REGISTRATION_DEADLINE).date()
    days_left = (deadline - today).days
    return {
        "today": today.isoformat(),
        "deadline": REGISTRATION_DEADLINE,
        "days_remaining": days_left,
        "status": "past_deadline" if days_left < 0 else "approaching" if days_left < 60 else "on_track",
        "regulator_portal": "https://www.ncsc.nl/onderwerpen/nis2",
    }


@mcp.tool()
def sign_readiness_attestation(entity_legal_name: str, kvk_number: str, controls_status: dict) -> dict:
    """
    Emit a HMAC-signed Wbni-2 readiness attestation for board sign-off.

    Args:
        entity_legal_name: Registered name.
        kvk_number: Dutch CoC.
        controls_status: Dict of NIS2 Article 21 risk-management measures + their status.

    Returns:
        {attestation, signature, verify_url}
    """
    att_id = f"WBNI2_{kvk_number}_{int(time.time())}_{os.urandom(4).hex()}"
    sealed = {
        "attestation_id": att_id,
        "spec": "NIS2_ART_21_NL_WBNI2",
        "entity_legal_name": entity_legal_name,
        "kvk_number": kvk_number,
        "controls_status": controls_status,
        "sealed_at": _ts(),
        "issuer": "MEOK AI Labs (CSOAI LTD)",
    }
    sig = _sign(sealed)
    return {
        "attestation_id": att_id,
        "attestation": sealed,
        "signature": sig,
        "verify_url": f"https://meok-attestation-api.vercel.app/verify/{att_id}",
        "board_sign_off_hint": "Print this attestation and have the named management-body member sign it. Wbni-2 §10 accountability is on the member.",
    }


if __name__ == "__main__":
    mcp.run()


# ── MEOK monetization layer (Stripe upgrade · PAYG · pricing) ──────────
# Free tier is zero-config. Upgrade to Pro (unlimited) or pay-as-you-go per call.
import os as _meok_os
MEOK_STRIPE_UPGRADE = "https://buy.stripe.com/00wfZjcgAeUW4c5cyQ8k90K"  # Pro (unlimited)
MEOK_PAYG_KEY = _meok_os.environ.get("MEOK_PAYG_KEY", "")  # set to enable PAYG (x402 / ~GBP0.05 per call)
MEOK_PRICING = "https://meok.ai/pricing"


def meok_upsell(tier: str = "free") -> dict:
    """Monetization options for free-tier callers: Pro upgrade, PAYG, or pricing page."""
    if tier != "free":
        return {}
    return {"upgrade_url": MEOK_STRIPE_UPGRADE,
            "payg_enabled": bool(MEOK_PAYG_KEY),
            "pricing": MEOK_PRICING}
