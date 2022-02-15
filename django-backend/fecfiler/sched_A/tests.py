from django.test import TestCase, Client


# initialize the APIClient app
client = Client()


class CreateNewSchedATest(TestCase):
    """Test module for inserting a sched_a item"""

    def setUp(self):
        self.valid_payload = {
            "aggregate_amt": None,
            "back_ref_sched_name": None,
            "back_ref_transaction_id": "none",
            "cmte_id": "C00658336",
            "contribution_amount": 100.00,
            "contribution_date": "2018-10-18",
            "create_date": "2019-02-28T03:01:55.412022",
            "delete_ind": None,
            "donor_cmte_id": None,
            "donor_cmte_name": None,
            "election_code": None,
            "election_other_description": None,
            "entity_id": "IND20190227000000149",
            "last_update_date": "2019-02-28T03:01:55.412022",
            "line_number": "11AI",
            "memo_code": None,
            "memo_text": "* Earmarked Contribution: See Below",
            "purpose_description": None,
            "report_id": 1,
            "transaction_id": "SA20190325000000001",
            "transaction_type": "15",
        }

        # invalid transaction_id
        self.invalid_payload = {
            "aggregate_amt": None,
            "back_ref_sched_name": None,
            "back_ref_transaction_id": None,
            "cmte_id": "C00658336",
            "contribution_amount": "100.00",
            "contribution_date": "2018-10-18",
            "create_date": "2019-02-28T03:01:55.412022",
            "delete_ind": None,
            "donor_cmte_id": None,
            "donor_cmte_name": None,
            "election_code": None,
            "election_other_description": None,
            "entity_id": "ORG20190227000000150",
            "last_update_date": "2019-02-28T03:01:55.412022",
            "line_number": "11AI",
            "memo_code": "X",
            "memo_text": "Note: Above Contribution earmarked through this organization.",
            "purpose_description": None,
            "report_id": 1,
            "transaction_id": "VVBSTFQ9X78E",
            "transaction_type": "15",
        }

    # def test_create_valid_sechdA_item(self):
    #     response = client.post(
    #         reverse('schedA'),
    #         data=json.dumps(self.valid_payload),
    #         content_type='application/json'
    #     )
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# Create your tests here.
