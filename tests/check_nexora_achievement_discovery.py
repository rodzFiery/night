"""NEXORA 71 — achievement collection is read-only and accurately counted."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from app.nexora_achievement_discovery import achievement_discovery, discovery_catalog


def test_catalog_is_unique_and_has_no_fake_worlds():
    catalog=discovery_catalog()
    assert len(catalog)==9
    assert len({entry["key"] for entry in catalog})==len(catalog)
    assert {entry["world"] for entry in catalog}=={"NEXORA","ASHFALL"}


def test_empty_collection_is_truthful():
    state=achievement_discovery({"events":[]})
    assert state["earned"]==0 and state["total"]==9 and state["percent"]==0
    assert all(not item["earned"] for item in state["goals"])


def test_collected_achievements_match_only_known_server_events():
    events=[
        {"world":"NEXORA","id":"nexora:first-arrival"},
        {"world":"ASHFALL","id":"ashfall:42:5"},
        {"world":"ASHFALL","id":"ashfall:43:5"},
        {"world":"ASHFALL","id":"ashfall:42:15"},
        {"world":"ASHFALL","id":"ashfall:42:99"},
    ]
    original=[dict(event) for event in events]
    state=achievement_discovery({"events":events})
    assert state["earned"]==3 and state["total"]==9
    assert state["percent"]==33
    assert [world["earned"] for world in state["worlds"]]==[1,2]
    assert events==original


def test_all_goals_complete_only_with_all_known_achievements():
    events=[
        {"world":"NEXORA","id":"nexora:"+key}
        for key in ("first-arrival","first-spark","level-ten","thousand-xp","daily-seven")
    ]+[
        {"world":"ASHFALL","id":"ashfall:42:"+str(level)}
        for level in (5,15,30,50)
    ]
    state=achievement_discovery({"events":events})
    assert state["earned"]==state["total"]==9
    assert state["percent"]==100


if __name__=="__main__":
    test_catalog_is_unique_and_has_no_fake_worlds()
    test_empty_collection_is_truthful()
    test_collected_achievements_match_only_known_server_events()
    test_all_goals_complete_only_with_all_known_achievements()
    print("NEXORA 71 achievement discovery checks passed")
