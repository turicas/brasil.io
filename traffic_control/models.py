import datetime
from copy import deepcopy
from itertools import chain

from django.db import models
from django.urls import reverse
from django.utils import timezone


class BlockRequestQuerySet(models.QuerySet):
    def from_hours_ago(self, hours):
        return self.filter(created_at__gte=timezone.now() - datetime.timedelta(hours=hours))

    def last_hour(self):
        return self.from_hours_ago(1)

    def last_day(self):
        return self.from_hours_ago(24)

    def today(self):
        today = timezone.now().date()
        return self.filter(created_at__year=today.year, created_at__month=today.month, created_at__day=today.day,)

    def yesterday(self):
        yesterday = timezone.now().date() - datetime.timedelta(days=1)
        return self.filter(
            created_at__year=yesterday.year, created_at__month=yesterday.month, created_at__day=yesterday.day,
        )

    def count_by(self, field_name):
        return self.values(field_name).annotate(total=models.Count(field_name)).order_by("-total")


class BlockedRequest(models.Model):
    objects = BlockRequestQuerySet.as_manager()

    request_data = models.JSONField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.TextField(default="", null=True, blank=True, db_index=True)
    headers = models.JSONField(default=dict, null=True, blank=True)
    query_string = models.JSONField(default=dict, null=True, blank=True)
    path = models.TextField(default="", null=True, blank=True, db_index=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)

    @classmethod
    def from_request_data(cls, request_data):
        obj = cls(request_data=deepcopy(request_data))
        headers = {key.lower(): value for key, value in dict(request_data.pop("headers", [])).items()}
        query_string = dict(request_data.pop("query_string", []))

        obj.headers = headers
        obj.query_string = query_string
        obj.path = request_data.get("path", "")
        obj.user_agent = headers.get("user-agent")
        obj.source_ip = (
            headers.get("cf-connecting-ip", "").strip()
            or headers.get("x-forwarded-for", "").strip()  # noqa
            or request_data.get("http", {}).get("remote-addr", "").strip()  # noqa
            or None  # noqa
        )
        obj.status_code = request_data.get("response_status_code", 1)

        return obj

    @classmethod
    def blocked_ips(cls, hourly_max=30, daily_max=1200, hours_ago=None):
        hours = hours_ago or 1
        hours_max = hourly_max * hours
        qs_hour = cls.objects.from_hours_ago(hours).count_by("source_ip").filter(total__gte=hours_max)
        qs_day = cls.objects.last_day().count_by("source_ip").filter(total__gte=daily_max)
        for blocked in chain(qs_hour, qs_day):
            ip = blocked["source_ip"]
            if ":" in ip:
                ip = ":".join(ip.split(":")[:4] + [":/64"])
            blocked["ip"] = ip
            yield blocked

    class Meta:
        ordering = ["-created_at"]


class DataUrlRedirect(models.Model):
    dataset_prev = models.SlugField(default="")
    dataset_dest = models.SlugField(default="")

    tablename_prev = models.SlugField(default="")
    tablename_dest = models.SlugField(default="")

    field_prev = models.SlugField(default="")
    field_dest = models.SlugField(default="")

    @property
    def redirect_map(self):
        return {
            reverse("core:dataset-detail", args=[self.dataset_prev]): reverse(
                "core:dataset-detail", args=[self.dataset_dest]
            ),
            reverse("core:dataset-files-detail", args=[self.dataset_prev]): reverse(
                "core:dataset-files-detail", args=[self.dataset_dest]
            ),
            reverse("api-v1:dataset-detail", args=[self.dataset_prev]): reverse(
                "api-v1:dataset-detail", args=[self.dataset_dest]
            ),
        }

    @classmethod
    def redirect_from(cls, path):
        redirects = {}

        for data_url_redirect in cls.objects.all().iterator():
            redirects.update(**data_url_redirect.redirect_map)

        return redirects.get(path, "")
