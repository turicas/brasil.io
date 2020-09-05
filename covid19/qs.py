from django.db.models import Q, QuerySet


class Covid19QuerySetMixin:
    def for_state(self, state):
        if state is None:
            return self
        return self.filter(state=state)


class Covid19BoletimQuerySet(Covid19QuerySetMixin, QuerySet):
    pass


class Covid19CasoQuerySet(Covid19QuerySetMixin, QuerySet):
    def city(self, imported=True):
        qs = self.filter(place_type="city")
        if not imported:
            qs = qs.filter(city_ibge_code__isnull=False)
        return qs

    def state(self):
        return self.filter(place_type="state")

    def lastest(self):
        return self.filter(is_last=True)

    def with_cases(self):
        qs = self.filter(confirmed__gt=0)
        qs = qs.exclude((Q(confirmed=0) | Q(confirmed__isnull=True)) & (Q(deaths=0) | Q(deaths__isnull=True)))
        return qs

    def with_deaths(self):
        return self.with_cases().filter(deaths__gt=0)

    def latest_city_cases(self):
        return self.with_cases().lastest().city(imported=False)

    def latest_state_cases(self):
        return self.with_cases().lastest().state()
