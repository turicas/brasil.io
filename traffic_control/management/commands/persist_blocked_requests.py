import json

from django.conf import settings
from django.core.management.base import BaseCommand
from django_redis import get_redis_connection
from tqdm import tqdm

from traffic_control.models import BlockedRequest


class Command(BaseCommand):
    help = "Read blocked requests from redis and persist them on potgres"

    def handle(self, *args, **kwargs):
        conn = get_redis_connection("default")
        all_requests = []
        cache_key = settings.RQ_BLOCKED_REQUESTS_LIST
        progress = tqdm("Reading requests...")
        while conn.llen(cache_key) > 0:
            data = json.loads(conn.lpop(cache_key))
            all_requests.append(data)
            progress.update()
        progress.close()

        print(f"Bulk inserting {len(all_requests)} entries")
        BlockedRequest.objects.bulk_create([BlockedRequest(request_data=req) for req in all_requests])
        print("Done")
