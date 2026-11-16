from .test_settings import *  # noqa: F403

DATABASES["default"]["NAME"] = BASE_DIR / ".public_demo_preview.sqlite3"
