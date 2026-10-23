from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import urlopen

from django.conf import settings
from django.http import HttpResponse


def build_document_source_url(document):
    if document.file_url:
        parsed = urlsplit(document.file_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return urlunsplit(
                (
                    parsed.scheme,
                    parsed.netloc,
                    quote(parsed.path, safe="/%"),
                    parsed.query,
                    parsed.fragment,
                )
            )

    if document.s3_key:
        base_url = f"{settings.S3_ENDPOINT_URL.rstrip('/')}/{settings.S3_BUCKET_NAME}"
        return f"{base_url}/{quote(document.s3_key, safe='/')}"

    raise ValueError("Document has no valid source URL")


def build_document_download_response(document):
    source_url = build_document_source_url(document)
    with urlopen(source_url, timeout=30) as remote_file:
        content = remote_file.read()

    filename = document.file_name or "document"
    response = HttpResponse(content, content_type="application/octet-stream")
    response["Content-Disposition"] = f"attachment; filename*=UTF-8''{quote(filename)}"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response
