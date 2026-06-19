from leads.access import status_matches


ALL_LEAD_STATUS_CHOICES = (
    ("Новая", "Новая"),
    ("БК", "БК"),
    ("Брак", "Брак"),
    ("Недозвон", "Недозвон"),
    ("Перезвон", "Перезвон"),
    ("Запись в офис", "Запись в офис"),
    ("Отказ", "Отказ"),
    ("Онлайн", "Онлайн"),
    ("Акт", "Акт"),
    ("Договор", "Договор"),
)

ROLE_STATUS_CHOICES = {
    "Администратор": ALL_LEAD_STATUS_CHOICES,
    "Директор КЦ": (
        ("Новая", "Новая"),
        ("Брак", "Брак"),
        ("Недозвон", "Недозвон"),
        ("Перезвон", "Перезвон"),
        ("Запись в офис", "Запись в офис"),
        ("Онлайн", "Онлайн"),
    ),
    "Оператор": (
        ("Новая", "Новая"),
        ("Брак", "Брак"),
        ("Недозвон", "Недозвон"),
        ("Перезвон", "Перезвон"),
        ("Запись в офис", "Запись в офис"),
        ("Онлайн", "Онлайн"),
    ),
    "Директор ЮПП": (
        ("Отказ", "Отказ"),
        ("Перезвон", "Перезвон"),
        ("Запись в офис", "Запись в офис"),
    ),
    "Юрист пирвичник": (
        ("Отказ", "Отказ"),
        ("Перезвон", "Перезвон"),
        ("Запись в офис", "Запись в офис"),
    ),
    "Менеджер": (
        ("Договор", "Договор"),
        ("Акт", "Акт"),
        ("Запись в офис", "Запись в офис"),
    ),
}


def get_status_choices_for_user(user):
    user_status = getattr(user, "status", "")
    for role_name, choices in ROLE_STATUS_CHOICES.items():
        if status_matches(user_status, role_name):
            return choices
    return ()


def get_allowed_status_values_for_user(user):
    return {value for value, _label in get_status_choices_for_user(user)}


def can_edit_status(user):
    return bool(get_status_choices_for_user(user))
