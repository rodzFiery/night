"""ASHFALL 7.6 battle engine tests: deterministic server-authoritative resolution."""
import unittest
from app.ashfall_battle_engine import resolve

class BattleEngineTests(unittest.TestCase):
 def test_victory(self):
  self.assertTrue(resolve(20,"infantry",28)["victory"])
 def test_defeat(self):
  self.assertFalse(resolve(1,"infantry",100)["victory"])
 def test_attack_increases_power(self):
  base=resolve(20,"hunter",100)
  buff=resolve(20,"hunter",100,0,{"attack":25})
  self.assertGreater(buff["player_power"],base["player_power"])
 def test_defense_reduces_losses(self):
  base=resolve(100,"rider",100)
  buff=resolve(100,"rider",100,0,{"defense":100})
  self.assertLessEqual(buff["losses"],base["losses"])
 def test_health_reduces_losses(self):
  base=resolve(100,"rider",100)
  buff=resolve(100,"rider",100,0,{"health":5000})
  self.assertLessEqual(buff["losses"],base["losses"])
 def test_losses_never_exceed_deployment(self):
  result=resolve(1,"hunter",100000)
  self.assertEqual(result["losses"],1)
  self.assertEqual(result["returned"],0)
 def test_zero_troops_rejected(self):
  with self.assertRaises(ValueError):resolve(0,"hunter",1)
 def test_unknown_unit_rejected(self):
  with self.assertRaises(ValueError):resolve(10,"dragon",1)
 def test_capacity_enforced(self):
  with self.assertRaises(ValueError):resolve(800,"infantry",1,0,{"march_capacity":100})
 def test_capacity_at_limit(self):
  self.assertEqual(resolve(350,"infantry",1,0,{"march_capacity":100})["capacity"],350)
 def test_no_hero_retains_base_limit(self):
  self.assertEqual(resolve(1000,"infantry",1)["capacity"],1000)
 def test_determinism(self):
  args=(50,"hunter",200,.2,{"attack":10,"defense":15,"health":1000})
  self.assertEqual(resolve(*args),resolve(*args))
 def test_power_bonus_applies(self):
  self.assertGreater(resolve(50,"infantry",50,.1)["player_power"],resolve(50,"infantry",50)["player_power"])

if __name__=="__main__":unittest.main()
