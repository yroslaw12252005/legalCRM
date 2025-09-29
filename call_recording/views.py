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

def get_calls(request):
    pass
    ## Первый запрос к API для получения списка абонентов
    #url = "https://cloudpbx.beeline.ru/apis/portal/abonents"
    #headers = {'X-MPBX-API-AUTH-TOKEN': MPBX_TOKEN}
    #get_abonents_response = requests.get(url, headers=headers)
#
    ## Проверяем успешность запроса
    #if get_abonents_response.status_code != 200:
    #    return render(request, 'call_recording.html', {'error': 'Не удалось получить данные абонентов'})
#
    ## Парсим JSON-ответ
    #abonents_data = get_abonents_response.json()
#
    ## Определяем, как получить список абонентов в зависимости от типа ответа
    #if isinstance(abonents_data, list):
    #    # Если API напрямую возвращает список
    #    abonents_list = abonents_data
    #elif isinstance(abonents_data, dict):
    #    # Если API возвращает словарь, ищем ключ 'data'
    #    abonents_list = abonents_data.get('data', [])
    #else:
    #    abonents_list = []
#
    #calls_data = []
#
    ## Обрабатываем каждого абонента
    #for abonent in abonents_list:
    #    # Формируем URL для получения записей разговоров
    #    user_id = abonent.get('userId')  # Используем .get() для безопасного доступа
    #    if not user_id:
    #        continue  # Пропускаем абонентов без user_id
#
    #    url = f"https://cloudpbx.beeline.ru/apis/portal/records?id=1&userId={user_id}&dateFrom=2025-09-26&dateTo=2025-09-27"
    #    headers = {'X-MPBX-API-AUTH-TOKEN': MPBX_TOKEN}
    #    response = requests.get(url, headers=headers)
#
    #    if response.status_code == 200:
    #        calls_data.append(response.json())
    #    else:
    #        calls_data.append({'error': f'Ошибка для user {user_id}'})
#
    #return render(request, 'call_recording.html', {'calls': calls_data})