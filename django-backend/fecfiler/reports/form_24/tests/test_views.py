from ..views import Form24ViewSet
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form24
from fecfiler.shared.viewset_test import FecfilerViewSetTest


class Form24ViewSetTest(FecfilerViewSetTest):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        user = User.objects.create(email="test@fec.gov", username="gov")
        super().set_default_user(user)
        super().set_default_committee(self.committee)
        super().setUp()

        self.test_name_1 = "test_name_1"
        self.test_name_2 = "test_name_2"
        self.test_name_3 = "test_name_3"

        self.f24_report_1 = create_form24(self.committee, data={"name": self.test_name_1})
        self.f24_report_2 = create_form24(self.committee, data={"name": self.test_name_2})
        self.f24_report_3 = create_form24(self.committee, data={"name": self.test_name_3})

    def test_names_happy_path(self):
        expected_json = [
            {
                "name": self.test_name_2,
            },
            {
                "name": self.test_name_3,
            },
        ]

        response = self.send_viewset_get_request(
            "/api/v1/reports/form-24/names/?exclude_ids=" + str(self.f24_report_1.id),
            Form24ViewSet,
            "names",
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)
