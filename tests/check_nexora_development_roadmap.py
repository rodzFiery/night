"""NEXORA 76 — roadmap priority, completeness and no-mutation checks."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.nexora_development_roadmap import development_roadmap


def fixture():
    levels={"hq":5,"farm":2,"lumber":3,"salvage":1,"fuel":5,"barracks":4}
    facilities=[{"key":key,"level":level,"remaining":max(0,5-level),"ready":level>=5}
                for key,level in levels.items()]
    return {"havens":[{"haven_id":7,"complete":False,"title":"First Foundations",
                       "target_level":5,"facilities":facilities}],
            "recommended_haven":7}


def test_lowest_level_first():
    data=fixture()
    before=[dict(item) for item in data["havens"][0]["facilities"]]
    result=development_roadmap(data)
    report=result["havens"][0]
    assert [step["key"] for step in report["steps"]]==["salvage","farm","lumber","barracks"]
    assert report["steps"][0]["next_level"]==2
    assert report["remaining_levels"]==10
    assert report["progress_percent"]==67
    assert data["havens"][0]["facilities"]==before
    assert result["no_automatic_construction"]


def test_complete_and_no_haven():
    assert development_roadmap({"havens":[],"recommended_haven":None})["havens"]==[]
    report=development_roadmap({"havens":[{"haven_id":1,"complete":True,
        "title":"Eternal Bastion"}],"recommended_haven":None})["havens"][0]
    assert report["complete"] and report["steps"]==[] and report["progress_percent"]==100


def test_invalid_input_fails_closed():
    for limit in (0,7,True):
        try:
            development_roadmap(fixture(),limit)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid roadmap limit accepted")
    data=fixture()
    data["havens"][0]["facilities"].pop()
    try:
        development_roadmap(data)
    except ValueError:
        pass
    else:
        raise AssertionError("Incomplete facility data accepted")


if __name__=="__main__":
    test_lowest_level_first()
    test_complete_and_no_haven()
    test_invalid_input_fails_closed()
    print("NEXORA 76 roadmap checks passed")
