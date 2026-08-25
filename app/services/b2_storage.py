import os
import uuid
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()


class B2Storage:

    def __init__(self):
        self.endpoint_url = os.getenv("B2_ENDPOINT_URL")
        self.key_id = os.getenv("B2_KEY_ID")
        self.application_key = os.getenv("B2_APPLICATION_KEY")
        self.bucket_name = os.getenv("B2_BUCKET_NAME")
        self.public_url = os.getenv("B2_PUBLIC_URL", "").rstrip("/")
        self.region = os.getenv("B2_REGION")

        required = {
            "B2_ENDPOINT_URL": self.endpoint_url,
            "B2_KEY_ID": self.key_id,
            "B2_APPLICATION_KEY": self.application_key,
            "B2_BUCKET_NAME": self.bucket_name,
            
        }

        missing = [
            name for name, value in required.items()
            if not value
        ]

        if missing:
            raise ValueError(
                f"Missing environment variables: {', '.join(missing)}"
            )

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.key_id,
            aws_secret_access_key=self.application_key,
            region_name=self.region,
        )

    # ---------------------------------------------------------
    # UPLOAD
    # ---------------------------------------------------------

    def upload_file(
        self,
        file,
        folder: str = "media",
    ) -> dict:

        original_filename = file.filename

        extension = Path(
            original_filename
        ).suffix.lower()

        unique_filename = (
            f"{uuid.uuid4().hex}{extension}"
        )

        file_key = f"{folder}/{unique_filename}"

        content_type = (
            file.content_type
            or "application/octet-stream"
        )

        try:

            self.client.upload_fileobj(
                file.file,
                self.bucket_name,
                file_key,
                ExtraArgs={
                    "ContentType": content_type
                },
            )

            return {
                "success": True,
                "file_key": file_key,
                "file_name": original_filename,
                "content_type": content_type,
                "url": self.get_public_url(file_key),
            }

        except ClientError as e:

            raise RuntimeError(
                f"B2 upload failed: {str(e)}"
            )

    # ---------------------------------------------------------
    # DELETE USING FILE KEY
    # ---------------------------------------------------------

    def delete_file(
        self,
        file_key: str,
    ) -> dict:

        try:

            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )

            return {
                "success": True,
                "file_key": file_key,
                "message": "File deleted successfully",
            }

        except ClientError as e:

            raise RuntimeError(
                f"B2 delete failed: {str(e)}"
            )

    # ---------------------------------------------------------
    # DELETE USING URL
    # ---------------------------------------------------------

    def delete_file_by_url(
        self,
        file_url: str,
    ) -> dict:

        file_key = self.extract_key_from_url(
            file_url
        )

        return self.delete_file(file_key)

    # ---------------------------------------------------------
    # PUBLIC URL
    # ---------------------------------------------------------

    def get_public_url(
        self,
        file_key: str,
    ) -> str:

        if not self.public_url:
            return file_key

        return f"{self.public_url}/{file_key}"

    # ---------------------------------------------------------
    # EXTRACT FILE KEY FROM URL
    # ---------------------------------------------------------

    def extract_key_from_url(
        self,
        file_url: str,
    ) -> str:

        parsed = urlparse(file_url)

        file_key = parsed.path.lstrip("/")

        if not file_key:
            raise ValueError(
                "Could not extract file key from URL"
            )

        return file_key

    # ---------------------------------------------------------
    # PRESIGNED DOWNLOAD URL
    # ---------------------------------------------------------

    def generate_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
    ) -> str:

        try:

            return self.client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_key,
                },
                ExpiresIn=expires_in,
            )

        except ClientError as e:

            raise RuntimeError(
                f"Failed to generate download URL: {str(e)}"
            )

    # ---------------------------------------------------------
    # CHECK FILE EXISTS
    # ---------------------------------------------------------

    def file_exists(
        self,
        file_key: str,
    ) -> bool:

        try:

            self.client.head_object(
                Bucket=self.bucket_name,
                Key=file_key,
            )

            return True

        except ClientError:

            return False