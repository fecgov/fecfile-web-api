from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from .models import CommitteeInfo


class CommitteeInfoTest(TestCase):
    """ Test module for CommitteeInfo model """

    def setUp(self):
        CommitteeInfo.objects.create(
            committeeid='C01234567', committeename = 'Test Committee 1', street1='Street1 ',
            street2 = 'Street 2', city='Washington DC', state='DC', zipcode='912853', text="-",
            treasurerfirstname='John', treasurerlastname='Smith', treasurerprefix='Mr')
            
        save_data = {
                "committeeid": "C11234567",
                "committeename": "Test Committee 2",
                "street1": "Street 1",
                "street2": "Street 2",
                "city": "Washington",
                "state": "DC",
                "text": "--",
                "zipcode": 20001,
                "treasurerprefix": "Mr",
                "treasurerfirstname": "John",
                "treasurermiddlename": "Doe",
                "treasurerlastname": "Smith",
                "treasurersuffix": "IV"
            }
        CommitteeInfo.objects.create(**save_data)
        
    def test_committee_create_partial_info(self):
        comm = CommitteeInfo.objects.get(committeeid='C01234567')
        
        self.assertEqual(comm.committeename, "Test Committee 1")

    def test_committee_create_full_info(self):
        comm = CommitteeInfo.objects.get(committeeid='C11234567')            
        self.assertEqual(comm.committeename, "Test Committee 2")
