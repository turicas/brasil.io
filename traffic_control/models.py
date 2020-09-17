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

    class Meta:
        ordering = ["-created_at"]
