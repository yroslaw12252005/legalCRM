import logging


logger = logging.getLogger(__name__)


def send_bulk_sms(records, message):
    sent_count = 0

    for record in records:
        phone = (record.phone or "").strip()
        if not phone:
            continue

        # Тестовая отправка: готово место для подключения реального SMS-провайдера.
        logger.info("Test SMS to %s for lead #%s: %s", phone, record.id, message)
        sent_count += 1

    return sent_count
