import asyncio
import json
import logging
import os
import re
import sys
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import requests
from aiobotocore.session import get_session
from botocore.exceptions import ClientError, ParamValidationError
from django.conf import settings
from django.utils import timezone

from company.models import Companys

from .models import CallRecording


MPBX_TOKEN = "d3ee5369-1e28-4039-999d-d92018c8988a"
BEELINE_RECORDING_POLL_SECONDS = 60
BEELINE_RECORDING_STATE_FILE = Path(settings.BASE_DIR) / ".beeline_recording_monitor_state.json"
BEELINE_RECORDING_LOCK_FILE = Path(settings.BASE_DIR) / ".beeline_recording_monitor.lock"
BEELINE_RECORDING_LOCK_STALE_SECONDS = 240
BEELINE_RECORDING_AUTO_MONITOR = True
# Add one entry per CRM company: company_id is from Companys.id.
# If all_operators is True, the monitor requests today's full Beeline abonent list every minute.
BEELINE_COMPANY_CONFIGS = [
    {
        "company_id": 1,
        "all_operators": True,
        "operators": [],
    },
]

logger = logging.getLogger(__name__)
_monitor_start_lock = threading.Lock()
_monitor_thread = None


class S3Client:
    def __init__(self, access_key, secret_key, endpoint_url, bucket_name):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": "ru-1",
        }
        self.bucket_name = bucket_name
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_bytes(self, data, key, content_type="audio/mpeg"):
        try:
            async with self.get_client() as client:
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                )
            return True
        except ParamValidationError:
            logger.exception("Invalid S3 config while uploading call recording")
            return False
        except ClientError:
            logger.exception("S3 upload failed for key %s", key)
            return False


s3_client = S3Client(
    access_key=settings.S3_ACCESS_KEY,
    secret_key=settings.S3_SECRET_KEY,
    endpoint_url=settings.S3_ENDPOINT_URL,
    bucket_name=settings.S3_BUCKET_NAME,
)


def s3_public_url(key):
    return f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET_NAME}/{quote(key, safe='/')}"


def normalize_phone(phone):
    digits = "".join(ch for ch in str(phone or "") if ch.isdigit())
    if not digits:
        return ""
    if len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"
    if len(digits) == 10:
        digits = f"7{digits}"
    return f"+{digits}"


def phone_for_filename(phone):
    normalized = normalize_phone(phone)
    return normalized.replace("+", "") or "unknown_phone"


def sanitize_path_part(value):
    cleaned = re.sub(r'[\\/:*?"<>|]+', "_", str(value or "").strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "unknown"


def parse_call_started_at(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def load_monitor_state():
    if not BEELINE_RECORDING_STATE_FILE.exists():
        return {"processed_ids": [], "monitor_date": ""}
    try:
        return json.loads(BEELINE_RECORDING_STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"processed_ids": [], "monitor_date": ""}


def save_monitor_state(state):
    BEELINE_RECORDING_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def build_company_folder(company):
    company_part = f"{company.id}_{sanitize_path_part(company.title)}"
    return f"{company_part}/Записи"


def build_recording_key(company, phone, call_started_at, external_id):
    started_at = call_started_at or timezone.now()
    timestamp = started_at.strftime("%Y%m%d_%H%M%S")
    filename = f"{phone_for_filename(phone)}_{timestamp}_{external_id}.mp3"
    return f"{build_company_folder(company)}/{filename}"


def fetch_abonents(session, headers):
    response = session.get("https://cloudpbx.beeline.ru/apis/portal/abonents", headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        abonents = payload
    elif isinstance(payload, dict):
        abonents = payload.get("data") or payload.get("abonents") or []
    else:
        abonents = []

    user_ids = []
    for abonent in abonents:
        user_id = str(abonent.get("userId") or "").strip()
        if user_id:
            user_ids.append(user_id)
    return user_ids


def resolve_operator_ids(config, session, headers):
    if config.get("all_operators"):
        return fetch_abonents(session, headers)
    return [operator for operator in config.get("operators", []) if operator]


def fetch_records_for_operator(session, operator, headers, date_from, date_to):
    url = (
        "https://cloudpbx.beeline.ru/apis/portal/records"
        f"?id=1&userId={operator}&dateFrom={date_from}&dateTo={date_to}"
    )
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("data") or payload.get("records") or []
    return []


def fetch_call_info(session, record_id, headers):
    url = f"https://cloudpbx.beeline.ru/apis/portal/v2/records/{record_id}?recordId={record_id}"
    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def download_recording_bytes(session, record_id, headers):
    url = f"https://cloudpbx.beeline.ru/apis/portal/v2/records/{record_id}/download?recordId={record_id}"
    response = session.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    return response.content


def create_recording_entry(company, external_id, call_info, audio_bytes):
    if CallRecording.objects.filter(external_id=external_id).exists():
        return "exists"

    phone = normalize_phone(call_info.get("phone"))
    if not phone:
        return "skipped"

    operator_phone = normalize_phone((call_info.get("abonent") or {}).get("phone"))
    call_started_at = parse_call_started_at(
        call_info.get("startDate") or call_info.get("createdAt") or call_info.get("date")
    )
    s3_key = build_recording_key(company, phone, call_started_at, external_id)
    uploaded = asyncio.run(s3_client.upload_bytes(audio_bytes, s3_key))
    if not uploaded:
        return "failed"

    CallRecording.objects.create(
        companys=company,
        phone=phone,
        operator_phone=operator_phone,
        external_id=external_id,
        file_name=s3_key.rsplit("/", 1)[-1],
        file_url=s3_public_url(s3_key),
        s3_key=s3_key,
        call_started_at=call_started_at,
    )
    return "created"


def run_monitor_iteration(session=None):
    if not MPBX_TOKEN:
        raise RuntimeError("MPBX_TOKEN is not configured")

    client = session or requests.Session()
    headers = {"X-MPBX-API-AUTH-TOKEN": MPBX_TOKEN}
    state = load_monitor_state()
    today = timezone.localdate() if settings.USE_TZ else datetime.now().date()
    today_key = today.isoformat()
    if state.get("monitor_date") != today_key:
        state = {"processed_ids": [], "monitor_date": today_key}
    processed_ids = set(state.get("processed_ids", []))

    date_from = today
    date_to = today

    result = {"processed": 0, "created": 0, "exists": 0, "skipped": 0, "failed": 0}

    for config in BEELINE_COMPANY_CONFIGS:
        company = Companys.objects.filter(id=config["company_id"]).first()
        if company is None:
            continue

        operator_ids = resolve_operator_ids(config, client, headers)
        for operator in operator_ids:
            records = fetch_records_for_operator(client, operator, headers, date_from, date_to)
            for raw_record in records:
                external_id = str(raw_record.get("recordId") or raw_record.get("id") or "").strip()
                if not external_id or external_id in processed_ids:
                    continue

                call_info = fetch_call_info(client, external_id, headers)
                audio_bytes = download_recording_bytes(client, external_id, headers)
                outcome = create_recording_entry(company, external_id, call_info, audio_bytes)

                result["processed"] += 1
                result[outcome] += 1
                if outcome != "failed":
                    processed_ids.add(external_id)

    state["processed_ids"] = list(processed_ids)[-3000:]
    state["monitor_date"] = today_key
    save_monitor_state(state)
    return result


def should_start_auto_monitor(argv=None):
    if not BEELINE_RECORDING_AUTO_MONITOR:
        return False

    argv = argv or sys.argv
    management_commands_to_skip = {
        "check",
        "collectstatic",
        "createsuperuser",
        "dbshell",
        "dumpdata",
        "flush",
        "loaddata",
        "makemigrations",
        "migrate",
        "shell",
        "showmigrations",
        "test",
    }
    current_command = argv[1] if len(argv) > 1 else ""

    if current_command in management_commands_to_skip:
        return False

    if current_command == "runserver" and os.environ.get("RUN_MAIN") != "true":
        return False

    return True


def acquire_monitor_lock():
    stale_seconds = max(BEELINE_RECORDING_LOCK_STALE_SECONDS, BEELINE_RECORDING_POLL_SECONDS * 4)
    lock_payload = {"pid": os.getpid(), "started_at": time.time()}

    try:
        fd = os.open(BEELINE_RECORDING_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
            json.dump(lock_payload, lock_file)
        return True
    except FileExistsError:
        try:
            lock_age_seconds = time.time() - BEELINE_RECORDING_LOCK_FILE.stat().st_mtime
            if lock_age_seconds > stale_seconds:
                BEELINE_RECORDING_LOCK_FILE.unlink(missing_ok=True)
                return acquire_monitor_lock()
        except OSError:
            logger.exception("Failed to inspect Beeline recording monitor lock file")
        return False


def release_monitor_lock():
    try:
        BEELINE_RECORDING_LOCK_FILE.unlink(missing_ok=True)
    except OSError:
        logger.exception("Failed to release Beeline recording monitor lock file")


def monitor_loop():
    session = requests.Session()
    poll_seconds = max(15, BEELINE_RECORDING_POLL_SECONDS)

    while True:
        if acquire_monitor_lock():
            try:
                result = run_monitor_iteration(session=session)
                logger.info(
                    "Beeline recording monitor processed=%s created=%s exists=%s skipped=%s failed=%s",
                    result["processed"],
                    result["created"],
                    result["exists"],
                    result["skipped"],
                    result["failed"],
                )
            except Exception:
                logger.exception("Beeline recording monitor iteration failed")
            finally:
                release_monitor_lock()
        time.sleep(poll_seconds)


def start_auto_monitor():
    global _monitor_thread

    if not should_start_auto_monitor():
        return False

    with _monitor_start_lock:
        if _monitor_thread and _monitor_thread.is_alive():
            return False

        _monitor_thread = threading.Thread(
            target=monitor_loop,
            name="beeline-recording-auto-monitor",
            daemon=True,
        )
        _monitor_thread.start()
        logger.info("Beeline recording auto monitor started")
        return True
