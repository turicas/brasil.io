import json

from brazil_data.states import STATES
from covid19.google_data import get_state_data_from_google_spreadsheets

output = "/data/old-data.json"
data = {}
for state in STATES:
    state = state.acronym
    print(state)

    data[state] = None
    while data[state] is None:
        try:
            data[state] = get_state_data_from_google_spreadsheets(state, timeout=10)
        except KeyboardInterrupt:
            break
        except:
            print("  error, trying again")
            continue
        else:
            for report in data[state]["reports"]:
                report["date"] = str(report["date"])
print("dumping")
with open(output, mode="w") as fobj:
    json.dump(data, fobj)
