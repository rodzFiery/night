"""NEXORA 74 — pursuit recommendations remain deterministic and read-only."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.nexora_achievement_discovery import achievement_discovery
from app.nexora_achievement_pursuits import achievement_pursuits


def discovery(events):
    return achievement_discovery({"events":events})


def test_first_pursuits_are_grounded():
    report=achievement_pursuits(discovery([]))
    assert report["remaining"]==9 and not report["complete"]
    assert [p["key"] for p in report["pursuits"]]==[
        "nexora:first-arrival","ashfall:level:5","nexora:first-spark"
    ]
    assert report["pursuits"][1]["destination"]=="/ashfall"


def test_next_ashfall_milestone_is_sequential():
    events=[{"world":"ASHFALL","id":"ashfall:8:5"},
            {"world":"ASHFALL","id":"ashfall:8:15"}]
    report=achievement_pursuits(discovery(events))
    ashfall=[p for p in report["pursuits"] if p["world"]=="ASHFALL"]
    assert len(ashfall)==1 and ashfall[0]["key"]=="ashfall:level:30"


def test_full_collection_has_no_pursuits():
    events=[{"world":"NEXORA","id":"nexora:"+key}
            for key in ("first-arrival","first-spark","level-ten","thousand-xp","daily-seven")]
    events += [{"world":"ASHFALL","id":"ashfall:8:"+str(level)}
               for level in (5,15,30,50)]
    report=achievement_pursuits(discovery(events))
    assert report["complete"] and report["remaining"]==0
    assert report["pursuits"]==[]


def test_pursuits_do_not_mutate_collection():
    state=discovery([])
    before=[dict(goal) for goal in state["goals"]]
    assert achievement_pursuits(state)==achievement_pursuits(state)
    assert state["goals"]==before
    for invalid in (0,13,True):
        try:
            achievement_pursuits(state,invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid pursuit limit accepted")


if __name__=="__main__":
    test_first_pursuits_are_grounded()
    test_next_ashfall_milestone_is_sequential()
    test_full_collection_has_no_pursuits()
    test_pursuits_do_not_mutate_collection()
    print("NEXORA 74 pursuit checks passed")
