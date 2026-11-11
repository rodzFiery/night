"""ASHFALL 4.4 theater development advisory tests."""
import unittest
from app.ashfall_theater_development import theater_development

def theater(charted=0, threat=None, resource=None):
    return {"id":"T-11","charted":charted,"total":16,
            "average_known_threat":threat,"known_resource_focus":resource,
            "completion_percent":round(100*charted/16)}

class TheaterDevelopmentTests(unittest.TestCase):
    def test_unknown_theater_never_infers_resources(self):
        plan=theater_development([theater()])["plans"][0]
        self.assertEqual(plan["doctrine"],"SURVEY")
        self.assertEqual(plan["remaining_to_chart"],16)

    def test_high_known_threat_prioritizes_security(self):
        plan=theater_development([theater(4,4.2,"wood")])["plans"][0]
        self.assertEqual(plan["doctrine"],"SECURITY")

    def test_sparse_coverage_prioritizes_survey(self):
        plan=theater_development([theater(5,2,"metal")])["plans"][0]
        self.assertEqual(plan["doctrine"],"SURVEY")

    def test_known_resource_guides_industry(self):
        plan=theater_development([theater(12,2,"metal")])["plans"][0]
        self.assertEqual(plan["doctrine"],"INDUSTRY")
        self.assertTrue(plan["advisory_only"])

    def test_coverage_without_resource_guides_logistics(self):
        plan=theater_development([theater(16,2)])["plans"][0]
        self.assertEqual(plan["doctrine"],"LOGISTICS")
        self.assertEqual(plan["remaining_to_chart"],0)

if __name__=="__main__":
    unittest.main()
