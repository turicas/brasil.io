from datetime import timedelta

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

    def schedule(self, func, interval, scheduled_time):
        job = self.scheduler.schedule(
            scheduled_time=scheduled_time,
            func=func,
            interval=interval,
            repeat=None,
        )
        print(f"Task {func.__name__} scheduled as {job}")

    def handle(self, *args, **kwargs):
        for job in self.scheduler.get_jobs():
            self.scheduler.cancel(job)

        # Adia 5min para dar margem ao restart de worker/scheduler. Sem isso, workers ainda com `tasks` da versão
        # anterior podem pegar um job recém-criado e quebrar.
        primeira_execucao = timezone.now() + timedelta(minutes=5)
        self.schedule(tasks.persist_blocked_requests_task, 300, primeira_execucao)
        self.schedule(tasks.update_blocked_ips_task, 3600, primeira_execucao)
        self.schedule(tasks.deactivate_abusive_users_task, 3600, primeira_execucao)
