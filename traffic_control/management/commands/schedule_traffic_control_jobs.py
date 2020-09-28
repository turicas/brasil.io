import django_rq
from cached_property import cached_property
from django.core.management.base import BaseCommand
from django.utils import timezone

from traffic_control import tasks


class Command(BaseCommand):
    help = "Schedule recurrent traffic control jobs"

    @cached_property
    def scheduler(self):
        return django_rq.get_scheduler("default")

    def schedule(self, func, interval):
        job = self.scheduler.schedule(scheduled_time=timezone.now(), func=func, interval=interval, repeat=None,)
        print(f"Task {func.__name__} scheduled as {job}")

    def handle(self, *args, **kwargs):
        for job in self.scheduler.get_jobs():
            self.scheduler.cancel(job)

        self.schedule(tasks.persist_blocked_requests_task, 300)
        self.schedule(tasks.update_blocked_ips_task, 3600)
