import asyncio
from contextlib import asynccontextmanager

from aiobotocore.session import get_session
from botocore.exceptions import ClientError


class S3Client:
    def __init__(
            self,
            access_key: str,
            secret_key: str,
            endpoint_url: str,
            bucket_name: str,
    ):
        self.config = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "region_name": "ru-1"
        }
        self.bucket_name = bucket_name
        self.session = get_session()

    @asynccontextmanager
    async def get_client(self):
        async with self.session.create_client("s3", **self.config) as client:
            yield client

    async def upload_file(
            self,
            file_path: str,
    ):

        object_name = file_path.split("/")[-1]
        print(file_path)# /users/artem/cat.jpg
        try:
            async with self.get_client() as client:
                with open('rrr.txt', "rb") as file:
                    await client.put_object(
                        Bucket=self.bucket_name,
                        Key=object_name,
                        Body=file,
                    )
                print(f"File {object_name} uploaded to {self.bucket_name}")
        except ClientError as e:
            print(f"Error uploading file: {e}")

    async def delete_file(self, object_name: str):
        try:
            async with self.get_client() as client:
                await client.delete_object(Bucket=self.bucket_name, Key=object_name)
                print(f"File {object_name} deleted from {self.bucket_name}")
        except ClientError as e:
            print(f"Error deleting file: {e}")

    async def get_file(self, object_name: str, destination_path: str):
        try:
            async with self.get_client() as client:
                response = await client.get_object(Bucket=self.bucket_name, Key=object_name)
                data = await response["Body"].read()
                with open(destination_path, "wb") as file:
                    file.write(data)
                print(f"File {object_name} downloaded to {destination_path}")
        except ClientError as e:
            print(f"Error downloading file: {e}")


async def main():
    s3_client = S3Client(
        access_key="EEFJDEUXC1CROO48RUGL",
        secret_key="bOWBlZckIVapgodQAZ4X9cMeAWwQ1i9nZ8rBVppE",
        endpoint_url="https://s3.twcstorage.ru",  # для Selectel используйте https://s3.storage.selcloud.ru
        bucket_name="edb6a103-vsecrm",
    )

    # Проверка, что мы можем загрузить, скачать и удалить файл
    await s3_client.upload_file("rrr.txt")
    #await s3_client.get_file("rrr.txt", "text_local_file.pdf")
    #await s3_client.delete_file("Баннер-5.pdf")


if __name__ == "__main__":
    asyncio.run(main())