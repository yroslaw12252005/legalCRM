from .settings import *  # noqa: F403


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# The historical migration chain contains legacy defaults that SQLite cannot
# materialize. Tests build current local app schemas directly instead.
MIGRATION_MODULES = {
    "accounts": None,
    "call_recording": None,
    "company": None,
    "contract": None,
    "cost": None,
    "education": None,
    "felial": None,
    "leads": None,
    "marketplace": None,
    "smart_calendar": None,
    "tilda_integration": None,
    "todolist": None,
    "wallet": None,
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
