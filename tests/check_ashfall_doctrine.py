"""ASHFALL 44: deterministic doctrine rules, without database or HTTP dependencies."""
from app.ashfall_economy import DOCTRINES, DOCTRINE_BONUS, DOCTRINE_COOLDOWN, doctrine_status, production_per_hour, production_interval

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

def test_specialization_is_resource_specific():
    # A level 5 farm with research and alliance boosts: doctrine must stack
    # consistently, not replace previously earned progression bonuses.
    normal=production_per_hour(120,5,research_level=3,alliance_bonus=.15)
    focused=production_per_hour(120,5,research_level=3,alliance_bonus=.15,
                                doctrine_bonus=DOCTRINE_BONUS)
    assert abs(focused/normal-1.08)<1e-12
    assert production_per_hour(120,0,doctrine_bonus=.08)==0
    assert production_per_hour(120,5,research_level=3,alliance_bonus=.15)==normal

def test_fractional_offline_accrual():
    # Small intervals must add up to the same whole resources as one large
    # interval, without granting a bonus through repeated polling.
    rate=production_per_hour(120,3,doctrine_bonus=.08)
    whole,part=production_interval(rate,3600,0)
    assert whole==int(rate)
    assert 0<=part<1
    earned=0
    remainder=0.0
    for _ in range(120):
        gained,remainder=production_interval(rate,30,remainder)
        earned+=gained
    assert earned==whole
    assert abs(remainder-part)<1e-7
    gained,remainder=production_interval(rate,0,remainder)
    assert gained==0
    assert 0<=remainder<1

def test_switch_boundary_not_retroactive():
    # A doctrine change first settles elapsed production at the old rate.
    # The new focus applies only to time after the change.
    base=production_per_hour(100,1)
    boosted=production_per_hour(100,1,doctrine_bonus=DOCTRINE_BONUS)
    old_gain,fraction=production_interval(base,3600,0)
    new_gain,fraction=production_interval(boosted,3600,fraction)
    assert old_gain==100
    assert new_gain==108
    assert old_gain+new_gain==208

if __name__=="__main__":
    test_unselected_haven()
    test_active_specialization_and_cooldown()
    test_specialization_is_resource_specific()
    test_fractional_offline_accrual()
    test_switch_boundary_not_retroactive()
    print("ASHFALL 44 doctrine rule tests passed")
