import datetime
from itertools import groupby

import rows


def state_deployed_data(state, start_date):
    deployed_state_spreadsheets = list(
        StateSpreadsheet.objects
        .filter(state=state, status=StateSpreadsheet.DEPLOYED)
        .order_by("date")
    )
    groups = groupby(deployed_state_spreadsheets, key=lambda row: row.date)
    has_city_data = {
        date: any(
            not sp.only_with_total_entry
            for sp in spreadsheets
        )
        for date, spreadsheets in groups
    }

    today = datetime.datetime.now().date()
    date = start_date
    one_day = datetime.timedelta(days=1)
    while date < today:
        city_data_for_state = has_city_data.get(date)
        if city_data_for_state is None:
            has_city_data[date] = False
        date += one_day

    return has_city_data


start_date = (
    StateSpreadsheet.objects
    .filter(status=StateSpreadsheet.DEPLOYED)
    .order_by("date")
    .values_list("date", flat=True)
    .first()
)
states = StateSpreadsheet.objects.order_by("state").distinct("state").values_list("state", flat=True)
filename = "/data/input/missing-city-data.csv"
writer = rows.utils.CsvLazyDictWriter(filename)
for state in states:
    data = state_deployed_data(state, start_date)
    for date, status in data.items():
        if status is False:
            writer.writerow({"state": state, "date": date})
