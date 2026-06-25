import time

from django.core.management.base import BaseCommand

from call_recording.services import (
    BEELINE_RECORDING_MONITOR_DATE,
    BEELINE_RECORDING_POLL_SECONDS,
    run_monitor_iteration,
)


class Command(BaseCommand):
    help = (
        "Постоянно опрашивает Beeline API по записям разговоров за "
        f"{BEELINE_RECORDING_MONITOR_DATE.strftime('%d.%m.%Y')} и загружает аудио."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Выполнить один цикл опроса и завершиться.",
        )
        parser.add_argument(
            "--poll-seconds",
            type=int,
            default=BEELINE_RECORDING_POLL_SECONDS,
            help="Интервал между опросами Beeline API в секундах.",
        )

    def handle(self, *args, **options):
        poll_seconds = max(5, options["poll_seconds"])
        run_once = options["once"]

        self.stdout.write(
            self.style.SUCCESS(
                "Beeline monitor started "
                f"for {BEELINE_RECORDING_MONITOR_DATE.strftime('%d.%m.%Y')}"
            )
        )

        while True:
            try:
                result = run_monitor_iteration()
                self.stdout.write(
                    f"date={BEELINE_RECORDING_MONITOR_DATE.isoformat()} "
                    f"processed={result['processed']} created={result['created']} "
                    f"exists={result['exists']} skipped={result['skipped']} "
                    f"failed={result['failed']}"
                )
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f"Beeline monitor error: {exc}"))

            if run_once:
                return

            time.sleep(poll_seconds)
