from model_bakery import baker

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, Group
from django.test import TestCase, RequestFactory

from covid19.context_processors import is_covid19_contributor


class TestCovid19ContributorContextProcessor(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/")
        self.rj_group = Group.objects.get(name__endswith="Rio de Janeiro")

    def test_false_if_user_is_not_logged_in(self):
        self.request.user = AnonymousUser()

        output = is_covid19_contributor(self.request)

        assert {"is_covid19_contributor": False} == output

    def test_false_if_user_does_not_have_permission(self):
        self.request.user = baker.make(settings.AUTH_USER_MODEL)

        output = is_covid19_contributor(self.request)

        assert {"is_covid19_contributor": False} == output

    def test_false_if_user_have_permission_but_is_not_staff(self):
        user = baker.make(settings.AUTH_USER_MODEL, is_staff=False)
        user.groups.add(self.rj_group)
        user.refresh_from_db()
        self.request.user = user

        output = is_covid19_contributor(self.request)

        assert {"is_covid19_contributor": False} == output

    def test_true_for_real_contributor(self):
        user = baker.make(settings.AUTH_USER_MODEL, is_staff=True)
        user.groups.add(self.rj_group)
        user.refresh_from_db()
        self.request.user = user

        output = is_covid19_contributor(self.request)

        assert {"is_covid19_contributor": True} == output

    def test_super_user_is_contributor(self):
        self.request.user = baker.make(settings.AUTH_USER_MODEL, is_superuser=True)

        output = is_covid19_contributor(self.request)

        assert {"is_covid19_contributor": True} == output

    def test_settings_is_correctly_configured(self):
        path = "covid19.context_processors.is_covid19_contributor"
        assert path in settings.TEMPLATES[0]["OPTIONS"]["context_processors"]
