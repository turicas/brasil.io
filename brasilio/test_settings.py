from .settings import RQ_QUEUES


for queue in RQ_QUEUES.values():
    queue["ASYNC"] = False
