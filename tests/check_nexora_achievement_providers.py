"""NEXORA 70 — provider validation and cross-world security invariants."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.nexora_achievement_providers import compose_chronicle, validate_event, normalize_timestamp


def event(world="ASHFALL", key="ashfall:1:5"):
    return {
        "id": key, "world": world, "title": "First Foundations",
        "description": "Earned from the authoritative settlement ledger.",
        "earned_at": 1767312000, "prestige": 100,
    }


def rejects(callback):
    try:
        callback()
    except (ValueError, OverflowError):
        return
    raise AssertionError("Invalid provider data was accepted")


def test_valid_provider_composition():
    def platform(db, user_id):
        assert user_id == 7
        return [event("NEXORA", "nexora:first-arrival")]
    def ashfall(db, user_id):
        return [event()]
    result=compose_chronicle(None,7,[("ASHFALL",ashfall),("NEXORA",platform)])
    assert len(result)==2
    assert {item["world"] for item in result}=={"ASHFALL","NEXORA"}
    assert all(item["earned_at"].endswith("+00:00") for item in result)


def test_cross_world_impersonation_rejected():
    rejects(lambda:compose_chronicle(None,7,[("NEXORA",lambda *_:[event()])]))
    rejects(lambda:compose_chronicle(None,7,[("ashfall",lambda *_:[])]))


def test_duplicate_ids_and_providers_rejected():
    rejects(lambda:compose_chronicle(None,7,[("ASHFALL",lambda *_:[event(),event()])]))
    rejects(lambda:compose_chronicle(None,7,[
        ("ASHFALL",lambda *_:[]),("ASHFALL",lambda *_:[])
    ]))


def test_invalid_payloads_rejected():
    for payload in [
        {**event(),"prestige":-1},
        {**event(),"prestige":True},
        {**event(),"id":"../../invalid"},
        {**event(),"title":""},
        {**event(),"earned_at":"not a timestamp"},
    ]:
        rejects(lambda payload=payload:validate_event(payload,"ASHFALL"))
    rejects(lambda:compose_chronicle(None,7,[("ASHFALL",lambda *_:None)]))


def test_provider_output_is_detached_and_deterministic():
    source=event()
    first=compose_chronicle(None,7,[("ASHFALL",lambda *_:[source])])
    source["title"]="Changed after projection"
    assert first[0]["title"]=="First Foundations"
    assert normalize_timestamp("2026-01-01T00:00:00Z")=="2026-01-01T00:00:00+00:00"


if __name__=="__main__":
    test_valid_provider_composition()
    test_cross_world_impersonation_rejected()
    test_duplicate_ids_and_providers_rejected()
    test_invalid_payloads_rejected()
    test_provider_output_is_detached_and_deterministic()
    print("NEXORA 70 provider contract checks passed")
