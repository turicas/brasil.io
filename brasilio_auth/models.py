from django.contrib.auth import get_user_model
from django.db import models


class NewsletterSubscriberQuerySet(models.QuerySet):
    def active(self):
        return self.filter(user__is_active=True)


class NewsletterSubscriber(models.Model):
    objects = NewsletterSubscriberQuerySet.as_manager()

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
