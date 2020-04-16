from django.db.models import Max, F

from core.models import Table

def get_covid19_cases_dataset():
    return Table.objects.for_dataset('covid19').named('caso').get_model()

def get_most_recent_city_entries_for_state(state):
    Covid19Cases = get_covid19_cases_dataset()
    return Covid19Cases.objects.order_by('-date').filter(
        state=state,
        place_type='city',
    ).annotate(last_date=Max('date')).filter(date=F('last_date'))
