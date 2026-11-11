"""ASHFALL 4.9 corridor graph tests."""
import unittest
from app.ashfall_relay_corridors import relay_corridors

class CorridorTests(unittest.TestCase):
    def test_empty_network(self):
        result=relay_corridors(set(),set())
        self.assertEqual(result["corridor_count"],0)
        self.assertEqual(result["largest_corridor_size"],0)

    def test_connected_chain(self):
        result=relay_corridors({(0,0),(1,0),(2,0)},set())
        self.assertEqual(result["corridor_count"],1)
        self.assertEqual(result["largest_corridor_size"],3)

    def test_diagonal_not_connected(self):
        result=relay_corridors({(0,0),(1,1)},set())
        self.assertEqual(result["corridor_count"],2)

    def test_separate_components(self):
        result=relay_corridors({(0,0),(1,0),(3,3)},set())
        self.assertEqual([c["size"] for c in result["corridors"]],[2,1])

    def test_unexplored_expansion_hidden(self):
        result=relay_corridors({(0,0)},set())
        self.assertEqual(result["expansion_opportunities"],[])

    def test_known_adjacent_expansion(self):
        result=relay_corridors({(0,0)}, {(1,0),(3,3)})
        self.assertEqual([r["id"] for r in result["expansion_opportunities"]],["T-21"])

    def test_bridge_priority(self):
        result=relay_corridors({(0,0),(2,0)}, {(1,0),(0,1)})
        self.assertEqual(result["expansion_opportunities"][0]["id"],"T-21")
        self.assertEqual(result["expansion_opportunities"][0]["priority"],"HIGH")

if __name__=="__main__":
    unittest.main()
