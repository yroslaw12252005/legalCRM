LEAD_TOPICS = [
    "ЗПП",
    "Уголовка",
    "Семейка",
    "Бонкродство",
    "Земля",
    "Жильщка",
    "Военка",
    "Наследка",
    "Администра",
    "Страховка",
    "ООО/ОАО",
    "Труды",
    "Арбитраж",
    "СНТ/ИЖС",
]


def status_variants(value):
    variants = {value}
    try:
        variants.add(value.encode("utf-8").decode("cp1251"))
    except Exception:
        pass
    try:
        variants.add(value.encode("cp1251").decode("utf-8"))
    except Exception:
        pass
    return variants


def status_matches(value, *targets):
    if not value:
        return False
    value_variants = status_variants(value)
    return any(value_variants & status_variants(target) for target in targets)


def build_topic_choices(existing_topics=()):
    topics = []
    seen = set()

    for topic in [*LEAD_TOPICS, *existing_topics]:
        normalized = (topic or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        topics.append(normalized)

    return topics


def can_view_phone(user, record, booking_come=None):
    phone = getattr(record, "phone", None)
    if not phone:
        return False

    if status_matches(getattr(record, "status", None), "Договор"):
        return True

    user_status = getattr(user, "status", None)
    if status_matches(user_status, "Директор ЮПП", "Юрист пирвичник"):
        return booking_come is True and status_matches(getattr(record, "status", None), "Онлайн")

    if status_matches(user_status, "Менеджер"):
        return booking_come is True

    return True


def get_phone_display(user, record, booking_come=None):
    if can_view_phone(user, record, booking_come=booking_come):
        return getattr(record, "phone", "-") or "-"
    return "-"


def can_transfer_to_representative(user, record):
    return status_matches(getattr(user, "status", None), "Директор ЮПП", "Администратор") and status_matches(
        getattr(record, "status", None), "Договор"
    )
