"""ASHFALL 3.6 connected frontier and distance scaling tests."""
import unittest
from app.ashfall_frontier import frontier_state, frontier_window, travel_duration

class FrontierTests(unittest.TestCase):
    def test_home_neighbors_are_available(self):
        self.assertEqual(frontier_state((8,8),set(),(9,8)),"available")
        self.assertEqual(frontier_state((8,8),set(),(10,8)),"locked")

    def test_discovery_extends_frontier(self):
        self.assertEqual(frontier_state((8,8),{(9,8)},(10,8)),"available")
        self.assertEqual(frontier_state((8,8),{(9,8)},(9,8)),"discovered")

    def test_world_boundaries(self):
        self.assertEqual(frontier_state((0,0),set(),(-1,0)),"invalid")
        self.assertEqual(frontier_state((15,15),set(),(16,15)),"invalid")
        self.assertEqual(frontier_state((0,0),set(),(1,1)),"available")

    def test_distance_cost(self):
        self.assertEqual(travel_duration(3,(8,8),(9,8)),180)
        self.assertEqual(travel_duration(3,(8,8),(10,8)),225)
        self.assertEqual(travel_duration(3,(8,8),(11,8)),270)

    def test_window_does_not_escape_world(self):
        window=frontier_window((0,0),set())
        self.assertEqual(len(window),16)
        self.assertTrue(all(0<=s["x"]<16 and 0<=s["y"]<16 for s in window))

if __name__=="__main__":
    unittest.main()
