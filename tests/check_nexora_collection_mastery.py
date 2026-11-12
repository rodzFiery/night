"""NEXORA 72 — collection mastery arithmetic and fail-closed checks."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from app.nexora_collection_mastery import collection_mastery


def state(earned,total=10):
    return collection_mastery({"earned":earned,"total":total})


def test_rank_thresholds():
    assert [state(value)["title"] for value in (0,2,4,6,8,10)]==[
        "Uncharted","Pathfinder","Wayfinder","Vanguard","Luminary","Chronicle Complete"
    ]


def test_next_rank_counts_are_exact():
    assert state(0)["remaining_to_next"]==2
    assert state(3)["next_goal"]==4
    assert state(3)["remaining_to_next"]==1
    assert state(10)["next_title"] is None
    assert state(10)["remaining_to_next"]==0
    assert all(rank["achieved"] for rank in state(10)["ranks"])


def test_small_catalog_rounding():
    report=state(1,9)
    assert report["next_goal"]==2
    assert report["remaining_to_next"]==1
    assert report["percent"]==11


def test_zero_catalog_is_not_marked_complete():
    report=state(0,0)
    assert report["title"]=="Uncharted"
    assert report["percent"]==0


def test_invalid_counts_rejected():
    for earned,total in ((-1,9),(10,9),(0,-1),(True,9),(0,1.5)):
        try:
            state(earned,total)
        except ValueError:
            continue
        raise AssertionError("Invalid mastery count accepted")


if __name__=="__main__":
    test_rank_thresholds()
    test_next_rank_counts_are_exact()
    test_small_catalog_rounding()
    test_zero_catalog_is_not_marked_complete()
    test_invalid_counts_rejected()
    print("NEXORA 72 mastery checks passed")
