from django.test import TestCase
from fecfiler.core.aggregation_helper import get_election_year, date_agg_format
import datetime


class SimpleTest(TestCase):
    def setUp(self):
        pass

    def test_get_election_year(self):
        result = get_election_year("H", "NJ", "01")
        self.assertGreater(len(result), 0, "did not get expected number of results from get_election_year")
        self.assertGreater(result[0], 1776, "Invalid election year - too long ago")

    def test_date_agg_format(self):
        self.assertEqual(date_agg_format("2022-11-17"), datetime.date(2022, 11, 17))
        self.assertEqual(date_agg_format("2022-11-07"), datetime.date(2022, 11, 7))
        self.assertEqual(date_agg_format("2022-02-07"), datetime.date(2022, 2, 7))
        self.assertEqual(date_agg_format("2022-2-7"), datetime.date(2022, 2, 7))
