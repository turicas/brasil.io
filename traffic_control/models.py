from django.db import models


class BlockedRequest(models.Model):
    request_data = models.JSONField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.TextField(default="", null=True, blank=True)
    headers = models.JSONField(default=dict, null=True, blank=True)
    query_string = models.JSONField(default=dict, null=True, blank=True)
    path = models.TextField(default="", null=True, blank=True, db_index=True)
    source_ip = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True, db_index=True)

    @classmethod
    def from_request_data(cls, request_data):
        obj = cls(request_data=request_data)
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

    class Meta:
        ordering = ["-created_at"]
