from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm


class EmailAdminAuthenticationForm(AdminAuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "Email"
        self.fields["username"].widget.input_type = "email"
        self.fields["username"].widget.attrs["autocomplete"] = "email"


admin.site.login_form = EmailAdminAuthenticationForm
