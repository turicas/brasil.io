import datetime
import itertools

from django.utils import timezone

from core.models import Table


def recent_activities(days_ago=30, limit=None):
    days_ago = timezone.now() - datetime.timedelta(days=30)
    tables_recently_updated = (
        Table.objects.filter(import_date__gte=days_ago).order_by("-import_date").select_related("dataset")
    )

    activities = []
    datasets_with_updates = []
    for metadata, tables in itertools.groupby(
        tables_recently_updated, key=lambda t: (t.dataset.slug, t.import_date.date())
    ):
        dataset_slug, date = metadata
        if dataset_slug in datasets_with_updates:
            continue
        tables = list(tables)
        name = tables[0].dataset.name
        plural = len(tables) > 1
        activities.append(
            {
                "date": date,
                "description": f"Tabela{'s' if plural else ''} {', '.join(t.name for t in tables)} atualizadas no dataset {name}",
            }
        )
        datasets_with_updates.append(dataset_slug)

    return activities[:limit]
