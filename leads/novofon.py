import base64
import hashlib
import hmac
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone

from company.models import Companys
from felial.models import Felial
from leads.models import Record


NOVOFON_API_BASE_URL = "https://api.novofon.com"
NOVOFON_PBX_STATS_METHOD = "/v1/statistics/pbx/"
NOVOFON_STATE_FILE = Path(settings.BASE_DIR) / ".novofon_monitor_state.json"
NOVOFON_DEFAULT_COMPANY_ID = int(os.getenv("NOVOFON_DEFAULT_COMPANY_ID", "1"))
NOVOFON_DEFAULT_FELIAL_ID = int(os.getenv("NOVOFON_DEFAULT_FELIAL_ID", "5"))
NOVOFON_API_KEY = os.getenv("NOVOFON_API_KEY", "appid_346882")
NOVOFON_API_SECRET = os.getenv("NOVOFON_API_SECRET", "uu9e61bqv98382tph38cpvgge6ievo4ohnyz7zsq")
NOVOFON_POLL_SECONDS = int(os.getenv("NOVOFON_POLL_SECONDS", "15"))
NOVOFON_INITIAL_LOOKBACK_SECONDS = int(os.getenv("NOVOFON_INITIAL_LOOKBACK_SECONDS", "120"))
NOVOFON_RECENT_IDS_LIMIT = 500
NOVOFON_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NOVOFON_LOCK_FILE = Path(settings.BASE_DIR) / ".novofon_monitor.lock"
NOVOFON_LOCK_STALE_SECONDS = int(os.getenv("NOVOFON_LOCK_STALE_SECONDS", "120"))
NOVOFON_AUTO_MONITOR = os.getenv("NOVOFON_AUTO_MONITOR", "true").lower() in {"1", "true", "yes", "on"}

logger = logging.getLogger(__name__)
_monitor_start_lock = threading.Lock()
_monitor_thread = None


def normalize_phone_value(phone):
    if not phone:
        return ""

    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if not digits:
        return ""

    return f"+{digits}"


def company_has_phone(company_id, normalized_phone):
    if not normalized_phone:
        return False

    existing_phones = Record.objects.filter(companys_id=company_id).values_list("phone", flat=True)
    return any(normalize_phone_value(existing_phone) == normalized_phone for existing_phone in existing_phones)


def build_auth_header(method_path, params, api_key, api_secret):
    sorted_items = sorted((key, value) for key, value in params.items())
    params_str = urlencode(sorted_items)
    signature_payload = f"{method_path}{params_str}{hashlib.md5(params_str.encode('utf-8')).hexdigest()}"
    signature = base64.b64encode(
        hmac.new(
            api_secret.encode("utf-8"),
            signature_payload.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")
    return {"Authorization": f"{api_key}:{signature}"}


def load_monitor_state(state_path=NOVOFON_STATE_FILE):
    if not state_path.exists():
        return {"last_end": None, "recent_ids": []}

    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"last_end": None, "recent_ids": []}


def save_monitor_state(state, state_path=NOVOFON_STATE_FILE):
    state_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")


def build_monitor_window(state, lookback_seconds=NOVOFON_INITIAL_LOOKBACK_SECONDS):
    now = timezone.localtime()
    if state.get("last_end"):
        start = datetime.fromisoformat(state["last_end"])
        if timezone.is_naive(start):
            start = timezone.make_aware(start, timezone.get_current_timezone())
        start = start - timedelta(seconds=30)
    else:
        start = now - timedelta(seconds=lookback_seconds)
    return start, now


def fetch_incoming_pbx_calls(api_key, api_secret, start_dt, end_dt, session=None):
    params = {
        "start": start_dt.strftime(NOVOFON_TIME_FORMAT),
        "end": end_dt.strftime(NOVOFON_TIME_FORMAT),
        "version": 2,
        "call_type": "in",
        "limit": 1000,
    }
    headers = build_auth_header(NOVOFON_PBX_STATS_METHOD, params, api_key, api_secret)
    client = session or requests
    response = client.get(
        f"{NOVOFON_API_BASE_URL}{NOVOFON_PBX_STATS_METHOD}",
        params=params,
        headers=headers,
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "success":
        raise RuntimeError(payload.get("message", "Novofon API returned error"))
    return payload.get("stats", [])


def ensure_default_entities():
    company = Companys.objects.filter(id=NOVOFON_DEFAULT_COMPANY_ID).first()
    felial = Felial.objects.filter(id=NOVOFON_DEFAULT_FELIAL_ID).first()
    if company is None or felial is None:
        raise RuntimeError("Default company or felial is not configured in database")
    return company, felial


def create_lead_from_incoming_call(call, company, felial):
    normalized_phone = normalize_phone_value(call.get("clid"))
    if not normalized_phone:
        return "skipped"

    if company_has_phone(company.id, normalized_phone):
        return "exists"

    Record.objects.create(
        phone=normalized_phone,
        where="Звонок",
        description=f"Входящий звонок Novofon monitor ({call.get('callstart', '')})",
        companys=company,
        felial=felial,
    )
    return "created"


def run_monitor_iteration(api_key, api_secret, state_path=NOVOFON_STATE_FILE, session=None):
    if not api_key or not api_secret:
        raise RuntimeError("NOVOFON_API_KEY or NOVOFON_API_SECRET is not configured")

    company, felial = ensure_default_entities()
    state = load_monitor_state(state_path=state_path)
    start_dt, end_dt = build_monitor_window(state)
    recent_ids = list(state.get("recent_ids", []))
    recent_ids_set = set(recent_ids)

    stats = fetch_incoming_pbx_calls(api_key, api_secret, start_dt, end_dt, session=session)

    result = {"processed": 0, "created": 0, "exists": 0, "skipped": 0, "window_start": start_dt, "window_end": end_dt}
    for call in stats:
        unique_call_id = str(call.get("pbx_call_id") or call.get("call_id") or "")
        if unique_call_id and unique_call_id in recent_ids_set:
            continue

        outcome = create_lead_from_incoming_call(call, company, felial)
        result["processed"] += 1
        result[outcome] += 1

        if unique_call_id:
            recent_ids.append(unique_call_id)
            recent_ids_set.add(unique_call_id)

    state["last_end"] = end_dt.isoformat()
    state["recent_ids"] = recent_ids[-NOVOFON_RECENT_IDS_LIMIT:]
    save_monitor_state(state, state_path=state_path)
    return result


def should_start_auto_monitor(argv=None):
    if not NOVOFON_AUTO_MONITOR:
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
        "monitor_novofon_calls",
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


def acquire_monitor_lock(lock_path=NOVOFON_LOCK_FILE):
    stale_seconds = max(NOVOFON_LOCK_STALE_SECONDS, NOVOFON_POLL_SECONDS * 4)
    lock_payload = {"pid": os.getpid(), "started_at": time.time()}

    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
            json.dump(lock_payload, lock_file)
        return True
    except FileExistsError:
        try:
            lock_age_seconds = time.time() - lock_path.stat().st_mtime
            if lock_age_seconds > stale_seconds:
                lock_path.unlink(missing_ok=True)
                return acquire_monitor_lock(lock_path=lock_path)
        except OSError:
            logger.exception("Failed to inspect Novofon monitor lock file")
        return False


def release_monitor_lock(lock_path=NOVOFON_LOCK_FILE):
    try:
        lock_path.unlink(missing_ok=True)
    except OSError:
        logger.exception("Failed to release Novofon monitor lock file")


def monitor_loop():
    api_key = NOVOFON_API_KEY
    api_secret = NOVOFON_API_SECRET
    poll_seconds = max(5, NOVOFON_POLL_SECONDS)
    session = requests.Session()

    while True:
        if acquire_monitor_lock():
            try:
                result = run_monitor_iteration(api_key, api_secret, session=session)
                logger.info(
                    "Novofon monitor window=%s..%s processed=%s created=%s exists=%s skipped=%s",
                    result["window_start"].strftime("%Y-%m-%d %H:%M:%S"),
                    result["window_end"].strftime("%Y-%m-%d %H:%M:%S"),
                    result["processed"],
                    result["created"],
                    result["exists"],
                    result["skipped"],
                )
            except Exception:
                logger.exception("Novofon monitor iteration failed")
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
            name="novofon-auto-monitor",
            daemon=True,
        )
        _monitor_thread.start()
        logger.info("Novofon auto monitor started with poll interval %s seconds", max(5, NOVOFON_POLL_SECONDS))
        return True
