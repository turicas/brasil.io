from django.contrib import admin

from brasilio_auth.models import NewsletterSubscriber


class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['user']


admin.site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)
