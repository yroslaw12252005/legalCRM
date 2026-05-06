from .text_normalizer import repair_mojibake_text


class RequestUserTextNormalizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and getattr(user, "is_authenticated", False):
            for field_name in ("status", "username", "first_name", "last_name"):
                current = getattr(user, field_name, None)
                if not isinstance(current, str):
                    continue
                fixed = repair_mojibake_text(current)
                if fixed != current:
                    setattr(user, field_name, fixed)
        return self.get_response(request)
