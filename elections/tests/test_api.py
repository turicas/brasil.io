import pytest
from django.urls import reverse
from model_bakery import baker

from elections.models import Candidacy


@pytest.mark.django_db
class TestDetailCandidacy:
    url_name = "election:candidacy_detail"
    http_user_agent = "test"

    def test_get_detail_candidacy(self, client, settings):
        candidacy = baker.make(Candidacy, _fill_optional=True)

        url = reverse(self.url_name, kwargs={"pk": candidacy.pk})
        resp = client.get(url, HTTP_USER_AGENT="test-user-agent")
        expected_data = {}

        assert resp.status_code == 200
        assert resp.json() == expected_data
