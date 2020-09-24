from cached_property import cached_property
from django.conf import settings

from traffic_control.cloudflare import Cloudflare
from traffic_control.models import BlockedRequest


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
        self.log("Getting all already blocked ips...")
        blocked_ips = set(item["ip"] for item in self.cf.rules_list_items(self.account["id"], self.rule_list["id"]))
        ips_to_block -= blocked_ips

        self.log(f"Blocking {len(ips_to_block)} new ips...")
        operation_info = self.cf.add_rule_list_items(self.account["id"], self.rule_list["id"], ips_to_block)
        operation_id = operation_info["operation_id"]

        status = self.cf.get_operation_status(self.account["id"], operation_id)
        self.log(status)
