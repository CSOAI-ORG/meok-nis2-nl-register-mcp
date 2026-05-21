"""Smoke tests for meok-nis2-nl-register-mcp."""
import sys, os, inspect, traceback
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import (
    classify_entity,
    generate_registration_packet,
    list_sectors,
    check_deadline_status,
    sign_readiness_attestation,
    ANNEX_I_ESSENTIAL,
    ANNEX_II_IMPORTANT,
)


def test_classify_large_energy_company_is_essential():
    r = classify_entity("energie", headcount=500, annual_turnover_eur=80_000_000)
    assert r["classification"] == "essential"
    assert r["scope"] == "in_scope"
    assert r["regulator"] == "ACM"


def test_classify_medium_chemie_is_important():
    r = classify_entity("chemie", headcount=80, annual_turnover_eur=12_000_000)
    assert r["classification"] == "important"
    assert r["scope"] == "in_scope"


def test_classify_small_excluded():
    r = classify_entity("energie", headcount=20, annual_turnover_eur=3_000_000)
    assert r["scope"] == "out_of_scope"


def test_classify_unknown_sector():
    r = classify_entity("fishing-fleet", headcount=100, annual_turnover_eur=15_000_000)
    assert r["scope"] == "out_of_scope"


def test_generate_registration_packet():
    r = generate_registration_packet(
        entity_legal_name="Acme NL B.V.",
        kvk_number="12345678",
        sector_key="energie",
        headcount=500,
        annual_turnover_eur=80_000_000,
        primary_contact_email="cisco@acme.nl",
        management_body_member="J. Jansen, CEO",
        cisos_attestation=True,
    )
    assert r["packet"]["wbni_2_registration"]["kvk_number"] == "12345678"
    assert r["packet"]["wbni_2_registration"]["sector_classification"]["regulator"] == "ACM"
    assert "signature" in r


def test_list_sectors_has_both_annexes():
    r = list_sectors()
    assert "energie" in r["annex_i_essential"]
    assert "chemie" in r["annex_ii_important"]
    assert r["total_essential"] >= 8


def test_deadline_status_returns_days():
    r = check_deadline_status()
    assert "days_remaining" in r
    assert r["deadline"] == "2026-06-30"


def test_sign_readiness_attestation():
    r = sign_readiness_attestation("Acme NL B.V.", "12345678", {"art_21_a": "in_place", "art_21_b": "in_place"})
    assert r["attestation_id"].startswith("WBNI2_12345678_")
    assert "signature" in r


if __name__ == "__main__":
    g = dict(globals())
    fns = [v for k, v in g.items() if k.startswith("test_") and inspect.isfunction(v)]
    p = f = 0
    for fn in fns:
        try:
            fn(); print(f"OK {fn.__name__}"); p += 1
        except Exception as e:
            print(f"X  {fn.__name__}: {type(e).__name__}: {e}"); traceback.print_exc(); f += 1
    print(f"\n{p} passed, {f} failed")
