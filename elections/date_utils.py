from datetime import date, datetime


def get_age(dtob):
    today = date.today()
    try:
        age = today.year - dtob.year - ((today.month, today.day) < (dtob.month, dtob.day))
    except Exception:
        return None, None

    return dtob.strftime("%d/%m/%Y"), age
