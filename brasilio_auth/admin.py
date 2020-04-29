import csv

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from django.urls import path

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

    def export_subscribers_csv_view(self, request):

        @staff_member_required
        def view(request):
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

        return view(request)


class UserAdmin(BaseUserAdmin):
    list_filter = ('groups', 'is_staff', 'is_superuser', 'is_active')


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(NewsletterSubscriber, NewsletterSubscriberAdmin)
