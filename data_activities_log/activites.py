import datetime
from dataclasses import dataclass
from itertools import chain, groupby

import feedparser
import pytz
from cachetools import TTLCache, cached
from django.conf import settings
from django.utils import timezone

from core.models import Table


@dataclass
class Activity:
    title: str
    url: str
    created_at: datetime


def brasilio_blog_items():
    timezone = pytz.timezone(settings.TIME_ZONE)
    url = "https://blog.brasil.io/feed.rss"
    feed = feedparser.parse(url)
    for entry in feed["entries"]:
        dt = entry["published_parsed"]
        yield Activity(
            title=f"[Blog] {entry['title']}",
            url=entry["link"],
            created_at=datetime.datetime(dt.tm_year, dt.tm_mon, dt.tm_mday, dt.tm_hour, dt.tm_min, dt.tm_sec).replace(
                tzinfo=timezone
            ),
        )


def dataset_updates(days_ago):
    days_ago = timezone.now() - datetime.timedelta(days=days_ago)
    tables_recently_updated = (
        Table.objects.filter(import_date__gte=days_ago).order_by("-import_date").select_related("dataset")
    )

    datasets_with_updates = []
    for metadata, tables in groupby(tables_recently_updated, key=lambda t: (t.dataset.slug, t.import_date.date())):
        dataset_slug, date = metadata
        if dataset_slug in datasets_with_updates:
            continue
        datasets_with_updates.append(dataset_slug)

        tables = list(tables)
        dataset = tables[0].dataset
        plural = len(tables) > 1
        desc = (
            f"Tabela{'s' if plural else ''} {', '.join(t.name for t in tables)} atualizadas no dataset {dataset.name}"
        )

        yield Activity(
            title=desc, url=dataset.detail_url, created_at=max([t.import_date for t in tables]),
        )


@cached(cache=TTLCache(maxsize=10, ttl=3600))
def recent_activities(days_ago=30, limit=None):
    min_date = timezone.now() - datetime.timedelta(days=days_ago)
    data = []
    for acitivy in chain(brasilio_blog_items(), dataset_updates(days_ago)):
        if acitivy.created_at >= min_date:
            data.append(acitivy)

    return sorted(data, key=lambda a: a.created_at, reverse=True)[:limit]
