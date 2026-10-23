import logging
from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from botocore.exceptions import BotoCoreError, ClientError, ParamValidationError
from django.conf import settings


logger = logging.getLogger(__name__)


def document_storage_is_configured():
    return all(
        (
            getattr(settings, "S3_ACCESS_KEY", ""),
            getattr(settings, "S3_SECRET_KEY", ""),
            getattr(settings, "S3_ENDPOINT_URL", ""),
            getattr(settings, "S3_BUCKET_NAME", ""),
        )
    )


class DocumentStorage:
    def __init__(self):
        self.session = get_session()

    @asynccontextmanager
    async def client(self):
        async with self.session.create_client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,
            region_name="ru-1",
        ) as client:
            yield client

    async def upload_bytes(self, content, object_key, content_type=None):
        try:
            params = {
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": object_key,
                "Body": content,
            }
            if content_type:
                params["ContentType"] = content_type

            async with self.client() as client:
                await client.put_object(**params)
            return True
        except (BotoCoreError, ClientError, ParamValidationError, OSError):
            logger.exception("Unable to upload client document to S3")
            return False


document_storage = DocumentStorage()
