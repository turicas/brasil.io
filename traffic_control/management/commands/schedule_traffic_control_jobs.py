import django_rq
from django.core.management.base import BaseCommand
from django.utils import timezone

from traffic_control import tasks


class Command(BaseCommand):
    help = "Schedule recurrent traffic control jobs"

    def schedule(self, func, interval):
        scheduler = django_rq.get_scheduler("default")
        job = scheduler.schedule(
            scheduled_time=timezone.now(), func=tasks.persist_blocked_requests_task, interval=interval, repeat=None,
        )
        print(f"Task {func.__name__} scheduled as {job}")

    def handle(self, *args, **kwargs):
        self.schedule(tasks.persist_blocked_requests_task, 300)
        self.schedule(tasks.update_blocked_ips_task, 3600)
