from .settings import *


for queue in RQ_QUEUES.values():
    queue['ASYNC'] = False
