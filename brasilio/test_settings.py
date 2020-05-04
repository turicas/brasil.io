from .settings import *  # noqa
from pathlib import Path


for queue in RQ_QUEUES.values():  # noqa
    queue["ASYNC"] = False


SAMPLE_SPREADSHEETS_DATA_DIR = Path(BASE_DIR).joinpath("covid19", "tests", "data")  # noqa
