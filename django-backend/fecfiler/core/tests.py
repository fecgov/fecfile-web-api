from django.test import TestCase
from fecfiler.core.aggregation_helper import get_election_year


class SimpleTest(TestCase):
    def setUp(self):
        pass

    def test_get_election_year(self):
        result = get_election_year("H", "NJ", "01")
        self.assertGreater(len(result), 0, "did not get expected number of results from get_election_year")
        self.assertGreater(result[0], 1776, "Invalid election year - too long ago")

