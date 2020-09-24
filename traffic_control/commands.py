import json
from cached_property import cached_property
from django.conf import settings
from django_redis import get_redis_connection
from tqdm import tqdm

from traffic_control.cloudflare import Cloudflare
from traffic_control.models import BlockedRequest


class PersistBlockedRequestsCommand:

    @classmethod
    def execute(cls):
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
        BlockedRequest.objects.bulk_create([BlockedRequest.from_request_data(request_data=req) for req in all_requests])
        print("Done")


class UpdateBlockedIPsCommand:
    def __init__(self, account_name, rule_name):
        self.cf = Cloudflare(settings.CLOUDFLARE_AUTH_EMAIL, settings.CLOUDFLARE_AUTH_KEY)
        self.account_name = account_name
        self.rule_name = rule_name

    def log(self, msg):
        print(msg)

    @cached_property
    def account(self):
        for obj in self.cf.accounts():
            if obj["name"] == self.account_name:
                return obj

        raise ValueError(f"There's no Cloudflare account named {self.account_name}")

    @cached_property
    def rule_list(self):
        for obj in self.cf.rules_list(self.account["id"]):
            if obj["name"] == self.rule_name:
                return obj

        raise ValueError(f"There's no Rule List account named {self.rule_nane} from account {self.account_name}")

    @classmethod
    def execute(cls, account_name, rule_name, hourly_max=30, daily_max=1200):
        self = cls(account_name, rule_name)

        ips_to_block = set(blocked["ip"] for blocked in BlockedRequest.blocked_ips(hourly_max, daily_max))
        if not ips_to_block:
            self.log("There aren't new blocked requests to analyize.")
            return

        self.log("Getting all already blocked ips...")
        blocked_ips = set(item["ip"] for item in self.cf.rules_list_items(self.account["id"], self.rule_list["id"]))
        ips_to_block -= blocked_ips

        if ips_to_block:
            self.log(f"Blocking {len(ips_to_block)} new ips...")
            operation_info = self.cf.add_rule_list_items(self.account["id"], self.rule_list["id"], ips_to_block)
            operation_id = operation_info["operation_id"]
            status = self.cf.get_operation_status(self.account["id"], operation_id)
            self.log(status)
        else:
            self.log("There aren't new ips to block")
