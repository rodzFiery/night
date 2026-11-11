"""ASHFALL 3.8 route planning regression tests."""
import unittest
from app.ashfall_routes import plan_route

class StrategicRouteTests(unittest.TestCase):
    def test_home_is_zero_distance(self):
        route=plan_route((8,8),(8,8),set())
        self.assertEqual(route["path"],[])
        self.assertEqual(route["minimum_seconds"],0)

    def test_adjacent_unknown_sector_is_one_mission(self):
        route=plan_route((8,8),(9,8),set())
        self.assertEqual(route["unknown_steps"],1)
        self.assertEqual(route["minimum_seconds"],120)
        self.assertEqual(route["maximum_seconds"],240)

    def test_distant_route_has_connected_waypoints(self):
        route=plan_route((8,8),(12,11),set())
        previous=(8,8)
        for waypoint in route["path"]:
            point=(waypoint["x"],waypoint["y"])
            self.assertEqual(max(abs(point[0]-previous[0]),abs(point[1]-previous[1])),1)
            previous=point
        self.assertEqual(previous,(12,11))

    def test_known_waypoints_reduce_mission_count(self):
        route=plan_route((8,8),(10,8),{(9,8)})
        self.assertEqual(route["known_steps"],1)
        self.assertEqual(route["unknown_steps"],1)
        self.assertEqual(route["next_sector"],{"x":10,"y":8})

    def test_world_bounds_rejected(self):
        for target in [(-1,0),(16,0),(0,16)]:
            with self.assertRaises(ValueError):
                plan_route((8,8),target,set())

    def test_unknown_threat_not_exposed(self):
        route=plan_route((8,8),(9,8),set())
        self.assertNotIn("threat",str(route))
        self.assertLess(route["minimum_seconds"],route["maximum_seconds"])

if __name__=="__main__":
    unittest.main()
