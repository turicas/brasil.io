from model_bakery import baker
from localflavor.br.br_states import STATE_CHOICES

from django.conf import settings
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.test import TestCase

from covid19.forms import state_choices_for_user


class AvailableStatesForUserTests(TestCase):

    def setUp(self):
        self.user = baker.make(settings.AUTH_USER_MODEL)

    def test_super_user_can_acccess_all_states(self):
        self.user.is_superuser = True

        choices = state_choices_for_user(self.user)

        assert list(STATE_CHOICES) == choices

    def test_user_without_permissions_has_no_choices(self):
        choices = state_choices_for_user(self.user)

        assert [] == choices

    def test_return_choices_from_user_permissions(self):
        covid_perms = Permission.objects.filter(
            codename__startswith=settings.COVID_IMPORT_PERMISSION_PREFIX
        )
        assert covid_perms.count() == 27  # this test requires migrations
        perm_1, perm_2 = covid_perms.filter(Q(codename__endswith='SP') | Q(codename__endswith='RJ'))
        self.user.groups.add(perm_1.group_set.get())
        self.user.groups.add(perm_2.group_set.get())

        choices = state_choices_for_user(self.user)

        assert 2 == len(choices)
        assert ('RJ', 'Rio de Janeiro') in choices
        assert ('SP', 'São Paulo') in choices
