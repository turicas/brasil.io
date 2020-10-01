import datetime
import itertools
from dataclasses import dataclass

from django.utils import timezone

from core.models import Table


@dataclass
class Activity:
    title: str
    url: str
    created_at: datetime


def dataset_updates(days_ago):
    days_ago = timezone.now() - datetime.timedelta(days=30)
    tables_recently_updated = (
        Table.objects.filter(import_date__gte=days_ago).order_by("-import_date").select_related("dataset")
    )

    datasets_with_updates = []
    for metadata, tables in itertools.groupby(
        tables_recently_updated, key=lambda t: (t.dataset.slug, t.import_date.date())
    ):
        dataset_slug, date = metadata
        if dataset_slug in datasets_with_updates:
            continue
        datasets_with_updates.append(dataset_slug)

        tables = list(tables)
        dataset = tables[0].dataset
        plural = len(tables) > 1
        desc = f"Tabela{'s' if plural else ''} {', '.join(t.name for t in tables)} atualizadas no dataset {dataset.name}"

        yield Activity(
            title=desc,
            url="",
            created_at=max([t.import_date for t in tables]),
        )


def recent_activities(days_ago=30, limit=None):
    activities = list(dataset_updates(days_ago))
    return activities[:limit]
