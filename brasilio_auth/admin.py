import csv

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path
from django.http import StreamingHttpResponse

from brasilio_auth.models import NewsletterSubscriber
from brasilio_auth.services import subscribers_as_csv_rows


class Echo:
    def write(self, value):
        return value



class NewsletterSubscriberAdmin(admin.ModelAdmin):
    change_list_template = 'brasilio_auth/newslettersubscribers_change_list.html'
    list_display = ['user']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('export/', self.export_subscribers_csv_view, name='subscribers-export'),
        ]
        return my_urls + urls

    @staff_member_required
    def export_subscribers_csv_view(self, request):
        rows = subscribers_as_csv_rows()

        ### we can refactor this later
        ### copied from core/views.py
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer, dialect=csv.excel)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in rows),
            content_type="text/csv;charset=UTF-8",
        )
        response["Content-Disposition"] = 'attachment; filename="newsletter_subscribers.csv"'
        response.encoding = "UTF-8"
        return response


admin.site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)
