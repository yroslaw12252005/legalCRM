from django.shortcuts import render
from django.http import HttpRequest  
import requests
from django.shortcuts import render
# https://cloudpbx.beeline.ru/apis/portal/records?id=1&userId={operator}&dateFrom={today}&dateTo={tomorrow}

# https://cloudpbx.beeline.ru/apis/portal/v2/records/{call_id}?recordId={call_id}

# https://cloudpbx.beeline.ru/apis/portal/v2/records/{call_id}/download?recordId={call_id}

#Скрипт по манеторинг и возырату аудиозаписей

API_TOKEN = '7378138493:AAEa8cK3TfAKcpbnvRYjs_NrPPZ0cVKUqcY'
MPBX_TOKEN = 'd3ee5369-1e28-4039-999d-d92018c8988a'



from django.utils import timezone
from django.conf import settings
import os
import time
from datetime import timedelta


def get_calls(request):
    runs_param = request.GET.get('runs')
    interval_param = request.GET.get('interval')
    try:
        runs = int(runs_param) if runs_param is not None else 1
    except ValueError:
        runs = 1
    try:
        interval_seconds = int(interval_param) if interval_param is not None else 60
    except ValueError:
        interval_seconds = 60

    calls_data = []

    # Директория для сохранения аудиозаписей
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    recordings_dir = None
    if media_root:
        recordings_dir = os.path.join(media_root, 'call_recordings')
        os.makedirs(recordings_dir, exist_ok=True)

    headers = {'X-MPBX-API-AUTH-TOKEN': MPBX_TOKEN}

    for _ in range(max(1, runs)):
        # Первый запрос к API для получения списка абонентов
        url_abonents = "https://cloudpbx.beeline.ru/apis/portal/abonents"
        get_abonents_response = requests.get(url_abonents, headers=headers)

        # Проверяем успешность запроса
        if get_abonents_response.status_code != 200:
            calls_data.append({'error': 'Не удалось получить данные абонентов'})
            if runs <= 1:
                break
            time.sleep(interval_seconds)
            continue

        # Парсим JSON-ответ
        abonents_data = get_abonents_response.json()

        # Определяем, как получить список абонентов в зависимости от типа ответа
        if isinstance(abonents_data, list):
            abonents_list = abonents_data
        elif isinstance(abonents_data, dict):
            abonents_list = abonents_data.get('data', [])
        else:
            abonents_list = []

        # Даты за сегодня и завтра
        today = timezone.now().date()
        date_from = today
        date_to = today + timedelta(days=1)

        # Обрабатываем каждого абонента
        for abonent in abonents_list:
            user_id = abonent.get('userId')
            if not user_id:
                continue

            url_records = f"https://cloudpbx.beeline.ru/apis/portal/records?id=1&userId={user_id}&dateFrom={date_from}&dateTo={date_to}"
            response = requests.get(url_records, headers=headers)

            if response.status_code == 200:
                records_json = response.json()

                # Определяем список записей звонков из ответа
                if isinstance(records_json, list):
                    records_list = records_json
                elif isinstance(records_json, dict):
                    records_list = records_json.get('data') or records_json.get('records') or []
                else:
                    records_list = []

                for record in records_list:
                    record_id = record.get('recordId') or record.get('id')
                    if not record_id:
                        continue

                    download_url = f"https://cloudpbx.beeline.ru/apis/portal/v2/records/{record_id}/download?recordId={record_id}"

                    resp = requests.get(download_url, headers=headers, timeout=30, stream=True)
                    if resp.status_code != 200:
                        continue

                    if not recordings_dir:
                        continue

                    file_path = os.path.join(recordings_dir, f"{record_id}.mp3")
                    with open(file_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
            else:
                calls_data.append({'userId': user_id, 'error': f'Ошибка для user {user_id}'})

        if runs > 1:
            time.sleep(interval_seconds)

    return render(request, 'call_recording.html', {'calls': calls_data})