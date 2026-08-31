from datetime import timedelta

from cached_property import cached_property
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Count
from django.template.loader import render_to_string
from django.utils import timezone
from tqdm import tqdm

from traffic_control.blocked_list import blocked_requests
from traffic_control.cloudflare import Cloudflare
from traffic_control.models import BlockedRequest


class PersistBlockedRequestsCommand:
    @classmethod
    def execute(cls, batch_size=10):
        self = cls()
        requests, counter = [], 0

        progress = tqdm(desc="Reading requests...")
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


class DeactivateAbusiveUsersCommand:
    """Desativa contas, apaga tokens e notifica usuários com uso abusivo da API"""

    DEFAULT_BLOCK_REASONS = ("deep_pagination_not_allowed",)
    DEFAULT_MAX_DEACTIVATIONS = 20
    EMAIL_TEMPLATE_BASE = "traffic_control/emails/deactivation_email"

    @classmethod
    def execute(
        cls,
        hours_ago: int | None = None,
        threshold: int | None = None,
        dry_run: bool = False,
        block_reasons: list[str] | None = None,
        max_deactivations: int | None = None,
    ):
        hours_ago = hours_ago or settings.API_ABUSIVE_USER_WINDOW_HOURS
        threshold = threshold or settings.API_ABUSIVE_USER_THRESHOLD
        block_reasons = tuple(block_reasons) if block_reasons else cls.DEFAULT_BLOCK_REASONS
        max_deactivations = max_deactivations or cls.DEFAULT_MAX_DEACTIVATIONS
        candidates = cls._find_abusive_user_ids(hours_ago, threshold, block_reasons)

        if not candidates:
            print("Nenhum usuário abusivo identificado.")
            return

        print(
            f"Identificados {len(candidates)} candidatos (hours_ago={hours_ago}, threshold={threshold}, "
            f"block_reasons={list(block_reasons)}, max={max_deactivations}):"
        )
        for user_id, count in candidates:
            print(f"  user_id={user_id} blocks={count}")

        if dry_run:
            print("--dry-run: nenhuma ação executada.")
            return

        User = get_user_model()
        desativados = 0
        for user_id, count in candidates:
            if desativados >= max_deactivations:
                print(f"Limite de {max_deactivations} desativações atingido; restantes ficam para a próxima rodada.")
                break
            user = User.objects.filter(id=user_id, is_active=True).first()
            if user is None:
                continue
            with transaction.atomic():
                user.auth_tokens.all().delete()
                user.is_active = False
                user.save(update_fields=["is_active"])
                cls._send_ban_email(user, count, hours_ago)
            desativados += 1
            print(f"Usuário desativado: id={user.id} username={user.username} blocks={count}")
        print(f"Total desativados nesta execução: {desativados}")

    @classmethod
    def _find_abusive_user_ids(cls, hours_ago, threshold, block_reasons):
        cutoff = timezone.now() - timedelta(hours=hours_ago)
        rows = (
            BlockedRequest.objects.filter(
                created_at__gte=cutoff,
                user_id__isnull=False,
                block_reason__in=block_reasons,
            )
            .values("user_id")
            .annotate(total=Count("*"))
            .filter(total__gte=threshold)
            .order_by("-total")
        )
        return [(row["user_id"], row["total"]) for row in rows]

    @classmethod
    def _send_ban_email(cls, user, block_count, hours_ago):
        if not user.email:
            return

        context = {
            "username": user.username,
            "block_count": block_count,
            "hours": hours_ago,
            "EMAIL_SUBJECT_PREFIX": settings.EMAIL_SUBJECT_PREFIX,
        }
        subject = render_to_string(f"{cls.EMAIL_TEMPLATE_BASE}_subject.txt", context).strip()
        text_body = render_to_string(f"{cls.EMAIL_TEMPLATE_BASE}_body.txt", context)
        html_body = render_to_string(f"{cls.EMAIL_TEMPLATE_BASE}.html", context)
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_body, "text/html")
        email.send()
