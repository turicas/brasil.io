from django.db import models


class BlockedRequest(models.Model):
    request_data = models.JSONField(null=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
