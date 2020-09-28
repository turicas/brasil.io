from cached_property import cached_property
from django.conf import settings
from tqdm import tqdm

from traffic_control.blocked_list import blocked_requests
from traffic_control.cloudflare import Cloudflare
from traffic_control.models import BlockedRequest


class PersistBlockedRequestsCommand:
    @classmethod
    def execute(cls, batch_size=10):
        self = cls()
        requests, counter = [], 0

        progress = tqdm("Reading requests...")
        while len(blocked_requests):
            requests.append(blocked_requests.lpop())
            if len(requests) == batch_size:
                self.persist_requests(requests)
                counter += batch_size
                requests = []
            progress.update()

        if requests:
            self.persist_requests(requests)
            counter += len(requests)
            progress.update()
        progress.close()

        if counter:
            print(f"New {counter} BlockedRequests were created!")
        else:
            print("There aren't new blocked requests.")

    def persist_requests(self, requests):
        BlockedRequest.objects.bulk_create([BlockedRequest.from_request_data(r) for r in requests])


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
    def execute(cls, account_name, rule_name, hourly_max=30, daily_max=1200, hours_ago=None):
        self = cls(account_name, rule_name)

        ips_to_block = set(
            blocked["ip"] for blocked in BlockedRequest.blocked_ips(hourly_max, daily_max, hours_ago=hours_ago)
        )
        print(ips_to_block)
        if not ips_to_block:
            self.log("There aren't new blocked requests to analyize.")
            return

        self.log(f"Blocking {len(ips_to_block)} new ips...")
        operation_info = self.cf.add_rule_list_items(self.account["id"], self.rule_list["id"], ips_to_block)
        operation_id = operation_info["operation_id"]
        status = self.cf.get_operation_status(self.account["id"], operation_id)
        self.log(status)
