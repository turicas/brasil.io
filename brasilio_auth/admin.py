import csv

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse
from django.urls import path

from brasilio_auth.models import NewsletterSubscriber, NormalizedEmail
from brasilio_auth.services import subscribers_as_csv_rows
from project.utils.admin import ExportCsvMixin

admin.site.unregister(User)


class Echo:
    def write(self, value):
        return value


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    change_list_template = "brasilio_auth/newslettersubscribers_change_list.html"
    list_display = ["user", "user_is_active"]

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path("export/", self.export_subscribers_csv_view, name="subscribers-export"),
        ]
        return my_urls + urls

    def export_subscribers_csv_view(self, request):
        @staff_member_required
        def view(request):
            rows = subscribers_as_csv_rows()

            # we can refactor this later
            # copied from core/views.py
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

    def user_is_active(self, obj):
        return obj.user.is_active

    user_is_active.short_description = "Usuário ativo?"
    user_is_active.boolean = True


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_filter = ("groups", "is_staff", "is_superuser", "is_active")


@admin.register(NormalizedEmail)
class NormalizedEmailAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ("id", "value", "user")
    search_fields = ("value", "user__username", "user__email")
    list_filter = ("user__is_active",)
    ordering = ("value",)
    list_per_page = 500
    actions = ["export_as_csv"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
