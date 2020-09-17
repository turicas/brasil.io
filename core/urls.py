from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.urls import path, reverse_lazy
from ratelimit.decorators import ratelimit

from core.util import ratelimit_key

from . import views, views_special

sign_up_url = reverse_lazy("brasilio_auth:sign_up")


def limited_dataset_detail(request, slug, tablename):
    # cannot use @decorator syntax because reading from settings during import time
    # prevents django.test.override_settings from working as expected.
    # that's why I'm manually decorating the view in this custom view
    return ratelimit(key=ratelimit_key, rate=settings.RATELIMIT_RATE, block=settings.RATELIMIT_ENABLE)(
        views.dataset_detail
    )(request, slug=slug, tablename=tablename)


app_name = "core"
urlpatterns = [
    # Institutional pages
    path("", views.index, name="index"),
    path("contato/", views.contact, name="contact"),
    path("datasets/", views.dataset_list, name="dataset-list"),
    path("home/", views.home, name="home"),
    path("dataset/<slug>/", views.dataset_detail, name="dataset-detail"),
    path("dataset/<slug>/files/", views.dataset_files_detail, name="dataset-files-detail"),
    path("dataset/<slug>/<tablename>/", limited_dataset_detail, name="dataset-table-detail"),
    path("datasets/sugira/", views.dataset_suggestion, name="dataset-suggestion"),
    path("manifesto/", views.manifesto, name="manifesto"),
    path("colabore/", views.collaborate, name="collaborate"),
    path("doe/", views.donate, name="donate"),
    path("contribuidores/", views.contributors, name="contributors"),
    # Dataset-specific pages (specials)
    path("especiais/", views_special.index, name="specials"),
    path(
        "especiais/documento/<document>/",
        login_required(views_special.document_detail, login_url=sign_up_url),
        name="special-document-detail",
    ),
    path(
        "especiais/caminho/",
        login_required(views_special.trace_path, login_url=sign_up_url),
        name="special-trace-path",
    ),
    path(
        "especiais/grupos/",
        login_required(views_special.company_groups, login_url=sign_up_url),
        name="special-company-groups",
    ),
]
