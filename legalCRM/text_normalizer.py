from __future__ import annotations

from django.db import models


MOJIBAKE_HINTS = ("Р", "С", "Ð", "Ñ")
MOJIBAKE_BAD_CHARS = set("ЂЃ‚ѓ„…†‡€‰Љ‹ЊЌЋЏђ‘’“”•–—™љ›њќћџ")
RU_CHARS = set("АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя")


def _score_text(value: str) -> int:
    ru_count = sum(1 for ch in value if ch in RU_CHARS)
    bad_count = sum(1 for ch in value if ch in MOJIBAKE_BAD_CHARS)
    return ru_count - (bad_count * 3)


def repair_mojibake_text(value: str | None) -> str | None:
    if not value or not isinstance(value, str):
        return value

    if not any(ch in value for ch in MOJIBAKE_HINTS):
        return value

    candidates: list[str] = []
    for src_enc in ("cp1251", "latin1"):
        try:
            converted = value.encode(src_enc).decode("utf-8")
            candidates.append(converted)
        except UnicodeError:
            continue

    if not candidates:
        return value

    best = value
    best_score = _score_text(value)
    for candidate in candidates:
        score = _score_text(candidate)
        if score > best_score:
            best = candidate
            best_score = score

    return best


def normalize_instance_text_fields(instance: models.Model) -> list[str]:
    changed_fields: list[str] = []
    for field in instance._meta.fields:
        if not isinstance(field, (models.CharField, models.TextField)):
            continue
        current = getattr(instance, field.name, None)
        if not isinstance(current, str):
            continue
        fixed = repair_mojibake_text(current)
        if fixed != current:
            setattr(instance, field.name, fixed)
            changed_fields.append(field.name)
    return changed_fields
