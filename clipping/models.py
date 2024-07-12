import datetime

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Clipping(models.Model):
    date = models.DateField(null=False, blank=False, default=datetime.date.today)
    vehicle = models.CharField(max_length=100, null=True, blank=True)
    author = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=200, null=True, blank=True)
    category = models.CharField(max_length=100, null=True)
    url = models.URLField(null=False, blank=False, unique=True)
    published = models.BooleanField(default=False, blank=True)

    added_by = models.ForeignKey(get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title


class ClippingRelation(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey()

    clipping = models.ForeignKey(Clipping, on_delete=models.CASCADE)

    def __str__(self):
        return "Content: {} | Clipping: {}".format(self.content_object.name, self.clipping.title)

    class Meta:
        unique_together = ["content_type", "object_id", "clipping"]
