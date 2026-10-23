from django import forms
from django.core.validators import FileExtensionValidator


MAX_CLIENT_DOCUMENT_SIZE = 15 * 1024 * 1024


class ClientDocumentUploadForm(forms.Form):
    file = forms.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=["pdf", "doc", "docx", "jpg", "jpeg", "png"]
            )
        ]
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data["file"]
        if uploaded_file.size > MAX_CLIENT_DOCUMENT_SIZE:
            raise forms.ValidationError("Размер файла не должен превышать 15 МБ")
        return uploaded_file
