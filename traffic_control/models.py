from django.db import models


class BlockedRequest(models.Model):
    request_data = models.JSONField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    user_agent = models.TextField(default="")
    headers = models.JSONField(default=dict)
    query_string = models.JSONField(default=dict)
    path = models.TextField(default="")
    source_ip = models.GenericIPAddressField(null=True)
    status_code = models.PositiveSmallIntegerField(default=429)

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
            or headers.get("x-forwarded-for", "").strip()
            or request_data.get("http", {}).get("remote-addr", "").strip()
            or None
        )
        obj.status_code = request_data.get("response_status_code", 1)

        return obj

    class Meta:
        ordering = ["-created_at"]
