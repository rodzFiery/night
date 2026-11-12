"""ASHFALL 44: deterministic doctrine rules, without database or HTTP dependencies."""
from app.ashfall_economy import DOCTRINES, DOCTRINE_BONUS, DOCTRINE_COOLDOWN, doctrine_status

class FakeDB:
    def __init__(self, row=None):
        self.row=row
    def execute(self, sql, params):
        assert "ashfall_economic_doctrine" in sql
        return self
    def fetchone(self):
        return self.row

def test_unselected_haven():
    result=doctrine_status(FakeDB(),1,100000)
    assert result["focus"]=="balanced"
    assert result["resource"] is None
    assert result["can_change"]
    assert result["bonus"]==0

def test_active_specialization_and_cooldown():
    start=100000
    for focus,resource in DOCTRINES.items():
        result=doctrine_status(FakeDB({"focus":focus,"changed_at":start}),1,start+100)
        assert result["resource"]==resource
        assert result["bonus"]==(DOCTRINE_BONUS if resource else 0)
        assert not result["can_change"]
        assert result["next_change_at"]==start+DOCTRINE_COOLDOWN
        result=doctrine_status(FakeDB({"focus":focus,"changed_at":start}),1,start+DOCTRINE_COOLDOWN)
        assert result["can_change"]

if __name__=="__main__":
    test_unselected_haven()
    test_active_specialization_and_cooldown()
    print("ASHFALL 44 doctrine rule tests passed")
