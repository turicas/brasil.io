from .settings import *  # noqa


for queue in RQ_QUEUES.values():  # noqa
    queue["ASYNC"] = False
