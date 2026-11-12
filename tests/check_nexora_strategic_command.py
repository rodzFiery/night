"""NEXORA 79 — command overview consistency, fallback and no mutation."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.nexora_strategic_command import strategic_command_overview


def fixtures():
    discovery={"earned":2,"total":9,"percent":22}
    mastery={"title":"Pathfinder"}
    pursuits={"pursuits":[{"title":"First Foundations","world":"ASHFALL","objective":"Build all facilities"}]}
    intelligence={"recommended_haven":4,"haven_count":1}
    roadmap={"havens":[{"haven_id":4,"title":"First Foundations","progress_percent":40,
                        "remaining_levels":18,"steps":[{"key":"farm","name":"Farm","next_level":3}]}]}
    forecast={"havens":[{"haven_id":4,"quotes":[{"key":"farm","affordable":False}]}]}
    readiness={"havens":[{"haven_id":4,"quotes":[{"key":"farm","status":"production_estimate",
        "estimated_hours":2.5,"limiting_resource":"wood"}]}]}
    return [discovery,mastery,pursuits,intelligence,roadmap,forecast,readiness]


def test_projection():
    inputs=fixtures()
    before=repr(inputs)
    result=strategic_command_overview(*inputs)
    assert result["collection"]["earned"]==2
    assert result["pursuit"]["world"]=="ASHFALL"
    assert result["settlement"]["haven_id"]==4
    assert result["upgrade"]["estimated_hours"]==2.5
    assert result["read_only"]
    assert repr(inputs)==before


def test_empty_player():
    data=fixtures()
    data[0]={"earned":0,"total":9,"percent":0}
    data[2]={"pursuits":[]}
    data[3]={"recommended_haven":None,"haven_count":0}
    for index in (4,5,6):
        data[index]={"havens":[]}
    result=strategic_command_overview(*data)
    assert result["pursuit"] is None
    assert result["settlement"] is None
    assert result["upgrade"] is None


def test_mismatched_haven_rejected():
    data=fixtures()
    data[6]={"havens":[]}
    try:
        strategic_command_overview(*data)
    except ValueError:
        pass
    else:
        raise AssertionError("Inconsistent strategic report accepted")


if __name__=="__main__":
    test_projection()
    test_empty_player()
    test_mismatched_haven_rejected()
    print("NEXORA 79 strategic command checks passed")
