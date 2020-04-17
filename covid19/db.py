from itertools import groupby

from core.models import Table


def get_covid19_cases_dataset():
    return Table.objects.for_dataset('covid19').named('caso').get_model()


def get_most_recent_city_entries_for_state(state, date):
    return _get_latest_cases(state, date, "city")


def get_most_recent_state_entry(state, date):
    return _get_latest_cases(state, date, "state")


def _get_latest_cases(state, date, place_type):
    Covid19Cases = get_covid19_cases_dataset()
    cases = Covid19Cases.objects.filter(
        state=state,
        date__lt=date,
        place_type=place_type,
    ).iterator()

    place_key_func = lambda row: (row.place_type, row.state, row.city)  # noqa
    order_func = lambda row: row.order_for_place  # noqa
    cases = sorted(cases, key=place_key_func)

    result = []
    for place_key, entries in groupby(cases, key=place_key_func):
        entries = sorted(entries, key=order_func, reverse=True)
        result.append(entries[0])

    if place_type == "state" and result:
        assert len(result) == 1
        result = result[0]

    return result
