from django.test import RequestFactory, TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from rest_framework.test import force_authenticate

from fecfiler.user.models import User


class FecfilerViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.default_user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.default_committee = CommitteeAccount.objects.get(committee_id="C01234567")
        self.factory = RequestFactory()

    def send_viewset_get_request(
        self,
        uri,
        viewset_class,
        action_name,
        **kwargs,
    ):
        request = self.factory.get(uri)
        self.init_request(request)
        response = viewset_class.as_view({"get": action_name})(request, **kwargs)
        return response

    def send_viewset_post_request(
        self,
        uri,
        data,
        viewset_class,
        action_name,
        authenticate=True,
        user=None,
        committee=None,
        **kwargs,
    ):
        request = self.factory.post(uri, data)
        self.init_request(
            request, authenticate=authenticate, user=user, committee=committee
        )
        response = viewset_class.as_view({"post": action_name})(request, **kwargs)
        return response

    def send_viewset_put_request(
        self,
        uri,
        data,
        content_type,
        viewset_class,
        action_name,
        authenticate=True,
        user=None,
        committee=None,
        **kwargs,
    ):
        request = self.factory.put(uri, data, content_type)
        self.init_request(
            request, authenticate=authenticate, user=user, committee=committee
        )
        response = viewset_class.as_view({"put": action_name})(request, **kwargs)
        return response

    def send_viewset_delete_request(
        self,
        uri,
        viewset_class,
        action_name,
        **kwargs,
    ):
        request = self.factory.delete(uri)
        self.init_request(request)
        response = viewset_class.as_view({"delete": action_name})(request, **kwargs)
        return response

    def init_request(self, request, authenticate=True, user=None, committee=None):
        if authenticate:
            request_user = user if user is not None else self.default_user
            request.user = request_user
            force_authenticate(request, request_user)

            request_committee = (
                committee if committee is not None else self.default_committee
            )
            request.session = {
                "committee_uuid": str(request_committee.id),
                "committee_id": str(request_committee.committee_id),
            }
