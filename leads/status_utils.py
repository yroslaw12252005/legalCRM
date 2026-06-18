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

COMMON_LEAD_STATUS_CHOICES = tuple(
    choice for choice in ALL_LEAD_STATUS_CHOICES if choice[0] not in {"БК", "Брак"}
)


def get_status_choices_for_user(user):
    status = getattr(user, "status", "")

    if status == "Администратор":
        return ALL_LEAD_STATUS_CHOICES

    if status in {"Директор КЦ", "Оператор"}:
        return (
            ("Новая", "Новая"),
            ("Брак", "Брак"),
            *tuple(choice for choice in COMMON_LEAD_STATUS_CHOICES if choice[0] != "Новая"),
        )

    return (
        ("Новая", "Новая"),
        ("БК", "БК"),
        *tuple(choice for choice in COMMON_LEAD_STATUS_CHOICES if choice[0] != "Новая"),
    )


def get_allowed_status_values_for_user(user):
    return {value for value, _label in get_status_choices_for_user(user)}
