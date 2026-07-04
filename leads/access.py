LEAD_TOPICS = [
    "Р—РџРџ",
    "РЈРіРѕР»РѕРІРєР°",
    "РЎРµРјРµР№РєР°",
    "Р‘РѕРЅРєСЂРѕРґСЃС‚РІРѕ",
    "РќР°Р»РѕРіРё",
    "Р“СЂР°Р¶РґР°РЅСЃС‚РІРѕ",
    "Р‘Р°РЅРєРё",
    "Р—РµРјР»СЏ",
    "Р–РёР»СЊС‰РєР°",
    "Р’РѕРµРЅРєР°",
    "РќР°СЃР»РµРґРєР°",
    "РђРґРјРёРЅРёСЃСЃС‚СЂР°",
    "РЎС‚СЂР°С…РѕРІРєР°",
    "РћРћРћ/РћРђРћ",
    "РўСЂСѓРґС‹",
    "РђСЂР±РёС‚СЂР°Р¶",
    "РЎРќРў/РР–РЎ",
    "РђРІС‚Рѕ",
    "Р”СЂСѓРіРѕРµ",
    "РњРёРіСЂР°С†РёСЏ",
    "РЎРѕС†РёР°Р»РєР°",
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


def build_source_choices(existing_sources=()):
    sources = []
    seen = set()

    for source in [*LEAD_SOURCES, *existing_sources]:
        normalized = (source or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        sources.append(normalized)

    return sources


def can_view_phone(user, record, booking_come=None):
    phone = getattr(record, "phone", None)
    if not phone:
        return False

    if status_matches(getattr(record, "status", None), "Р”РѕРіРѕРІРѕСЂ"):
        return True

    user_status = getattr(user, "status", None)
    if status_matches(user_status, "Р”РёСЂРµРєС‚РѕСЂ Р®РџРџ", "Р®СЂРёСЃС‚ РїРёСЂРІРёС‡РЅРёРє"):
        return booking_come is True or status_matches(getattr(record, "status", None), "РћРЅР»Р°Р№РЅ", "Р”РѕРіРѕРІРѕСЂ")

    if status_matches(user_status, "РњРµРЅРµРґР¶РµСЂ"):
        return booking_come is True

    return True


def get_phone_display(user, record, booking_come=None):
    if can_view_phone(user, record, booking_come=booking_come):
        return getattr(record, "phone", "-") or "-"
    return "-"


def can_transfer_to_representative(user, record):
    return status_matches(getattr(user, "status", None), "Р”РёСЂРµРєС‚РѕСЂ Р®РџРџ", "РђРґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ") and status_matches(
        getattr(record, "status", None), "Р”РѕРіРѕРІРѕСЂ"
    )
