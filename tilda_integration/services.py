import hashlib
import hmac
import json
import re
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from leads.models import Record

from .models import TildaIdempotencyKey


MAX_PAYLOAD_BYTES = getattr(settings, "TILDA_WEBHOOK_MAX_PAYLOAD_BYTES", 256 * 1024)
SYSTEM_FIELDS = {
    "test",
    "token",
    "csrfmiddlewaretoken",
    "id_company",
    "id_felial",
    "felial_id",
}
SENSITIVE_DESCRIPTION_FIELDS = {"cookies", "x-tilda-token"}


class TildaWebhookError(Exception):
    def __init__(self, code, status=400):
        self.code = code
        self.status = status
        super().__init__(code)


@dataclass
class ProcessingResult:
    lead: Record | None
    duplicate: bool
    external_id: str


def hash_secret(secret):
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        secret.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def secret_matches(secret, secret_hash):
    if not secret or not secret_hash:
        return False
    return hmac.compare_digest(hash_secret(secret), secret_hash)


def _clean_value(value):
    value = str(value).strip()
    return "".join(char for char in value if char in "\n\t" or ord(char) >= 32)


def parse_payload(request):
    content_length = request.META.get("CONTENT_LENGTH")
    try:
        if content_length and int(content_length) > MAX_PAYLOAD_BYTES:
            raise TildaWebhookError("payload_too_large", 413)
    except ValueError:
        raise TildaWebhookError("invalid_content_length", 400)

    content_type = (request.content_type or "").lower()
    if content_type == "application/json":
        if len(request.body) > MAX_PAYLOAD_BYTES:
            raise TildaWebhookError("payload_too_large", 413)
        try:
            raw = json.loads(request.body.decode(request.encoding or "utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TildaWebhookError("invalid_json", 400)
        if not isinstance(raw, dict):
            raise TildaWebhookError("json_object_required", 400)
        payload = {}
        for key, value in raw.items():
            values = value if isinstance(value, list) else [value]
            cleaned = [_clean_value(item) for item in values if item is not None and _clean_value(item)]
            if cleaned:
                payload[str(key)] = cleaned
        return payload

    if content_type not in ("application/x-www-form-urlencoded", "multipart/form-data", ""):
        raise TildaWebhookError("unsupported_content_type", 415)

    payload = {}
    for key, values in request.POST.lists():
        cleaned = [_clean_value(item) for item in values if item and _clean_value(item)]
        if cleaned:
            payload[str(key)] = cleaned
    return payload


def first_value(payload, key):
    for existing_key, values in payload.items():
        if existing_key.casefold() == key.casefold() and values:
            return values[0]
    return ""


def supplied_token(request, payload):
    return request.headers.get("X-Tilda-Token", "") or first_value(payload, "token")


def _normalized_key(value):
    return re.sub(r"[^0-9a-zа-яё]+", "", str(value).casefold())


def _mapped_value(payload, aliases):
    normalized_aliases = {_normalized_key(alias) for alias in aliases}
    for key, values in payload.items():
        if _normalized_key(key) in normalized_aliases and values:
            return values[0]
    return ""


def normalize_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    if not 7 <= len(digits) <= 15:
        return None
    return "+" + digits


def normalize_email(value):
    value = (value or "").strip().casefold()
    if not value:
        return None
    try:
        validate_email(value)
    except ValidationError:
        return None
    return value


def _description(payload):
    lines = []
    for key, values in payload.items():
        normalized = key.casefold()
        if normalized in SYSTEM_FIELDS or normalized in SENSITIVE_DESCRIPTION_FIELDS:
            continue
        lines.append(f"{key}: {', '.join(values)}")
    return "\n".join(lines)[:5000]


def _external_id(integration, payload):
    tranid = first_value(payload, "tranid")
    if tranid:
        return tranid[:255]
    safe_payload = {
        key: values
        for key, values in payload.items()
        if key.casefold() not in SYSTEM_FIELDS and key.casefold() not in SENSITIVE_DESCRIPTION_FIELDS
    }
    canonical = json.dumps(safe_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    form_id = first_value(payload, "formid") or "no-form"
    ten_minute_bucket = int(timezone.now().timestamp()) // 600
    return f"fallback:{form_id}:{ten_minute_bucket}:{digest}"[:255]


def validate_form_id(integration, payload):
    allowed = integration.allowed_form_ids or []
    if allowed and first_value(payload, "formid") not in allowed:
        raise TildaWebhookError("form_not_allowed", 400)


def process_submission(integration, payload):
    validate_form_id(integration, payload)
    mapping = integration.field_mapping or {}
    name = _mapped_value(payload, mapping.get("name", []))
    phone_raw = _mapped_value(payload, mapping.get("phone", []))
    email_raw = _mapped_value(payload, mapping.get("email", []))
    phone = normalize_phone(phone_raw)
    email = normalize_email(email_raw)

    if not (name or phone or email):
        raise TildaWebhookError("contact_data_required", 400)

    external_id = _external_id(integration, payload)
    with transaction.atomic():
        try:
            with transaction.atomic():
                submission = TildaIdempotencyKey.objects.create(
                    integration=integration,
                    external_id=external_id,
                )
        except IntegrityError:
            return ProcessingResult(lead=None, duplicate=True, external_id=external_id)

        lead = Record.objects.create(
            name=(name or phone or email or "Tilda lead")[:50],
            phone=phone,
            email=email,
            description=_description(payload),
            where="Tilda",
            companys=integration.company,
            felial=integration.branch,
        )
        submission.lead = lead
        submission.save(update_fields=["lead"])

    return ProcessingResult(lead=lead, duplicate=False, external_id=external_id)
