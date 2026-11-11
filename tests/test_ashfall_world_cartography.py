"""ASHFALL 3.7 Atlas camera viewport regression tests."""
import unittest
from app.ashfall_frontier import atlas_viewport, frontier_state

class WorldCartographyTests(unittest.TestCase):
    def test_center_view_has_49_sectors(self):
        self.assertEqual(len(atlas_viewport(8,8)),49)

    def test_corner_view_is_clipped(self):
        self.assertEqual(len(atlas_viewport(0,0)),16)
        self.assertEqual(len(atlas_viewport(15,15)),16)

    def test_far_side_of_world_is_accessible(self):
        self.assertIn((15,15),atlas_viewport(15,15))
        self.assertNotIn((0,0),atlas_viewport(15,15))

    def test_camera_rejects_invalid_coordinates(self):
        for x,y in [(-1,0),(0,16),(16,0),(0,-1)]:
            with self.assertRaises(ValueError):
                atlas_viewport(x,y)

    def test_camera_does_not_unlock_frontier(self):
        self.assertEqual(frontier_state((8,8),set(),(15,15)),"locked")

if __name__=="__main__":
    unittest.main()
