LEAD_TOPICS = [
    "ЗПП",
    "Уголовка",
    "Семейка",
    "Банкротство",
    "Налоги",
    "Гражданство",
    "Банки",
    "Земля",
    "Жилищка",
    "Военка",
    "Наследка",
    "Административка",
    "Страховка",
    "ООО/ОАО",
    "Труды",
    "Арбитраж",
    "СНТ/ИЖС",
    "Авто",
    "Другое",
    "Миграция",
    "Социалка",
]

LEAD_SOURCES = [
    "VK",
    "Tilda",
    "РЕ",
    "Звонок",
    "Право",
    "Лакоста",
    "Марина",
]


def normalize_text(value):
    if not isinstance(value, str):
        return value

    normalized = value.strip()
    if not normalized:
        return normalized

    for _ in range(2):
        if "Р" not in normalized and "\x98" not in normalized:
            break
        try:
            raw = bytearray()
            for char in normalized:
                if char == "\x98":
                    raw.append(0x98)
                else:
                    raw.extend(char.encode("cp1251"))
            fixed = raw.decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            break
        if fixed == normalized:
            break
        normalized = fixed.strip()

    return normalized


def status_variants(value):
    normalized = normalize_text(value)
    variants = {normalized}
    try:
        variants.add(normalized.encode("utf-8").decode("cp1251"))
    except Exception:
        pass
    try:
        variants.add(normalized.encode("cp1251").decode("utf-8"))
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
        normalized = normalize_text(topic or "")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        topics.append(normalized)

    return topics


def build_source_choices(existing_sources=()):
    sources = []
    seen = set()

    for source in [*LEAD_SOURCES, *existing_sources]:
        normalized = normalize_text(source or "")
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        sources.append(normalized)

    return sources


def can_view_phone(user, record, booking_come=None):
    phone = getattr(record, "phone", None)
    if not phone:
        return False

    if status_matches(getattr(record, "status", None), "Договор"):
        return True

    user_status = getattr(user, "status", None)
    if status_matches(user_status, "Директор ЮПП", "Юрист пирвичник"):
        return booking_come is True or status_matches(getattr(record, "status", None), "Онлайн", "Договор")

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
