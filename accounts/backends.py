from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):
    """Authenticate active users by a case-insensitive email address."""

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        UserModel = get_user_model()
        email_address = (email or username or "").strip()

        if not email_address or password is None:
            return None

        users = list(
            UserModel._default_manager.filter(email__iexact=email_address)
        )
        if not users:
            # Keep password hashing time similar for existing and missing users.
            UserModel().set_password(password)
            return None

        matched_users = [
            user
            for user in users
            if user.check_password(password) and self.user_can_authenticate(user)
        ]
        # Legacy duplicate emails are allowed only when the password identifies
        # exactly one active account. Ambiguous credentials are always rejected.
        return matched_users[0] if len(matched_users) == 1 else None
