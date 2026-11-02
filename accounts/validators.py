from django.core.validators import RegexValidator


username_with_spaces_validator = RegexValidator(
    regex=r"^[\w.@+\- ]+\Z",
    message=(
        "Введите правильное имя пользователя. Оно может содержать буквы, "
        "цифры, пробелы и знаки @/./+/-/_."
    ),
    code="invalid",
)
