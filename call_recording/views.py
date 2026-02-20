import os
import time
from datetime import timedelta

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

MPBX_TOKEN = os.getenv("MPBX_TOKEN", "")


@login_required
def get_calls(request):
    if not MPBX_TOKEN:
        return render(request, "call_recording.html", {"calls": [{"error": "MPBX_TOKEN is not configured"}]})

    runs_param = request.GET.get("runs")
    interval_param = request.GET.get("interval")
    try:
        runs = int(runs_param) if runs_param is not None else 1
    except ValueError:
        runs = 1
    try:
        interval_seconds = int(interval_param) if interval_param is not None else 60
    except ValueError:
        interval_seconds = 60

    runs = max(1, min(runs, 3))
    interval_seconds = max(1, min(interval_seconds, 120))

    calls_data = []

    media_root = getattr(settings, "MEDIA_ROOT", None)
    recordings_dir = None
    if media_root:
        recordings_dir = os.path.join(media_root, "call_recordings")
        os.makedirs(recordings_dir, exist_ok=True)

    headers = {"X-MPBX-API-AUTH-TOKEN": MPBX_TOKEN}

    for _ in range(runs):
        url_abonents = "https://cloudpbx.beeline.ru/apis/portal/abonents"
        get_abonents_response = requests.get(url_abonents, headers=headers, timeout=20)

        if get_abonents_response.status_code != 200:
            calls_data.append({"error": "Не удалось получить данные абонентов"})
            if runs <= 1:
                break
            time.sleep(interval_seconds)
            continue

        abonents_data = get_abonents_response.json()

        if isinstance(abonents_data, list):
            abonents_list = abonents_data
        elif isinstance(abonents_data, dict):
            abonents_list = abonents_data.get("data", [])
        else:
            abonents_list = []

        today = timezone.now().date()
        date_from = today
        date_to = today + timedelta(days=1)

        for abonent in abonents_list:
            user_id = abonent.get("userId")
            if not user_id:
                continue

            url_records = f"https://cloudpbx.beeline.ru/apis/portal/records?id=1&userId={user_id}&dateFrom={date_from}&dateTo={date_to}"
            response = requests.get(url_records, headers=headers, timeout=20)

            if response.status_code == 200:
                records_json = response.json()

                if isinstance(records_json, list):
                    records_list = records_json
                elif isinstance(records_json, dict):
                    records_list = records_json.get("data") or records_json.get("records") or []
                else:
                    records_list = []

                for record in records_list:
                    record_id = record.get("recordId") or record.get("id")
                    if not record_id or not recordings_dir:
                        continue

                    download_url = f"https://cloudpbx.beeline.ru/apis/portal/v2/records/{record_id}/download?recordId={record_id}"

                    resp = requests.get(download_url, headers=headers, timeout=30, stream=True)
                    if resp.status_code != 200:
                        continue

                    file_path = os.path.join(recordings_dir, f"{record_id}.mp3")
                    with open(file_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
            else:
                calls_data.append({"userId": user_id, "error": f"Ошибка для user {user_id}"})

        if runs > 1:
            time.sleep(interval_seconds)

    return render(request, "call_recording.html", {"calls": calls_data})
