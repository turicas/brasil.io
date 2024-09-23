from datetime import date, datetime


def get_age(data_nascimento):
    today = date.today()
    try:
        dtob = datetime.strptime(data_nascimento, "%Y-%m-%d").date()
        age = today.year - dtob.year - ((today.month, today.day) < (dtob.month, dtob.day))
    except Exception:
        return None, None

    return dtob.strftime("%d/%m/%Y"), age
