import os
import time

from django.core.management.base import BaseCommand

from leads.novofon import NOVOFON_POLL_SECONDS, run_monitor_iteration


class Command(BaseCommand):
    help = "Постоянно опрашивает Novofon API по входящим звонкам и создает заявки для новых телефонов."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Выполнить один цикл опроса и завершиться.",
        )
        parser.add_argument(
            "--poll-seconds",
            type=int,
            default=NOVOFON_POLL_SECONDS,
            help="Интервал между опросами Novofon API в секундах.",
        )

    def handle(self, *args, **options):
        api_key = os.getenv("NOVOFON_API_KEY", "")
        api_secret = os.getenv("NOVOFON_API_SECRET", "")
        poll_seconds = max(5, options["poll_seconds"])
        run_once = options["once"]

        self.stdout.write(self.style.SUCCESS("Novofon monitor started"))

        while True:
            try:
                result = run_monitor_iteration(api_key, api_secret)
                self.stdout.write(
                    "window="
                    f"{result['window_start'].strftime('%Y-%m-%d %H:%M:%S')}..{result['window_end'].strftime('%Y-%m-%d %H:%M:%S')} "
                    f"processed={result['processed']} created={result['created']} "
                    f"exists={result['exists']} skipped={result['skipped']}"
                )
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"Novofon monitor error: {exc}"))

            if run_once:
                return

            time.sleep(poll_seconds)
