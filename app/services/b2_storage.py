import os
import uuid
from pathlib import Path
from urllib.parse import urlparse

from b2sdk.v2 import InMemoryAccountInfo, B2Api
from b2sdk.v2.exception import B2Error
from dotenv import load_dotenv

load_dotenv()


class B2Storage:

    def __init__(self):

        self.key_id = os.getenv("B2_KEY_ID")
        self.application_key = os.getenv("B2_APPLICATION_KEY")
        self.bucket_name = os.getenv("B2_BUCKET_NAME")
        self.public_url = os.getenv(
            "B2_PUBLIC_URL",
            ""
        ).rstrip("/")

        required = {
            "B2_KEY_ID": self.key_id,
            "B2_APPLICATION_KEY": self.application_key,
            "B2_BUCKET_NAME": self.bucket_name,
        }

        missing = [
            name
            for name, value in required.items()
            if not value
        ]

        if missing:
            raise ValueError(
                f"Missing environment variables: {', '.join(missing)}"
            )

        # ---------------------------------------------------------
        # B2 NATIVE API
        # ---------------------------------------------------------

        self.info = InMemoryAccountInfo()

        self.api = B2Api(
            self.info
        )

        self.api.authorize_account(
            "production",
            self.key_id,
            self.application_key,
        )

        self.bucket = self.api.get_bucket_by_name(
            self.bucket_name
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

        file_key = (
            f"{folder}/{unique_filename}"
        )

        content_type = (
            file.content_type
            or "application/octet-stream"
        )

        try:

            # Make sure we start from beginning
            file.file.seek(0)

            file_data = file.file.read()

            uploaded_file = self.bucket.upload_bytes(
                file_data,
                file_key,
                content_type=content_type,
            )

            return file_key

        except B2Error as e:

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

            # Find the latest version of this file
            file_versions = self.bucket.ls(
                file_key,
                latest_only=True,
            )

            file_version = None

            for version, _ in file_versions:
                file_version = version
                break

            if file_version is None:
                return {
                    "success": False,
                    "file_key": file_key,
                    "message": "File not found",
                }

            self.api.delete_file_version(
                file_version.id_,
                file_version.file_name,
            )

            return {
                "success": True,
                "file_key": file_key,
                "message": "File deleted successfully",
            }

        except B2Error as e:

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

        return self.delete_file(
            file_key
        )

    # ---------------------------------------------------------
    # PUBLIC URL
    # ---------------------------------------------------------

    def get_public_url(
        self,
        file_key: str,
    ) -> str:

        if not self.public_url:
            return file_key

        return (
            f"{self.public_url}/{file_key}"
        )

    # ---------------------------------------------------------
    # EXTRACT FILE KEY FROM URL
    # ---------------------------------------------------------

    def extract_key_from_url(
        self,
        file_url: str,
    ) -> str:

        parsed = urlparse(file_url)

        path = parsed.path.lstrip("/")

        if not path:
            raise ValueError(
                "Could not extract file key from URL"
            )

        # -----------------------------------------------------
        # If URL is our configured public URL
        # -----------------------------------------------------

        if self.public_url:

            public_parsed = urlparse(
                self.public_url
            )

            public_path = (
                public_parsed.path
                .strip("/")
            )

            if public_path and path.startswith(
                public_path + "/"
            ):

                return path[
                    len(public_path) + 1:
                ]

        # -----------------------------------------------------
        # Backblaze native download URL
        #
        # /file/bucket-name/path/to/file
        # -----------------------------------------------------

        file_prefix = "file/"

        if path.startswith(file_prefix):

            path = path[
                len(file_prefix):
            ]

            bucket_prefix = (
                f"{self.bucket_name}/"
            )

            if path.startswith(
                bucket_prefix
            ):

                return path[
                    len(bucket_prefix):
                ]

        # -----------------------------------------------------
        # S3-compatible URL
        #
        # /bucket-name/path/to/file
        # -----------------------------------------------------

        bucket_prefix = (
            f"{self.bucket_name}/"
        )

        if path.startswith(
            bucket_prefix
        ):

            return path[
                len(bucket_prefix):
            ]

        # -----------------------------------------------------
        # Otherwise assume the supplied path
        # itself is the file key.
        # -----------------------------------------------------

        return path

    # ---------------------------------------------------------
    # PRESIGNED / AUTHORIZED DOWNLOAD URL
    # ---------------------------------------------------------

    def generate_download_url(
        self,
        file_key: str,
        expires_in: int = 3600,
    ) -> str:

        try:

            authorization = self.bucket.get_download_authorization(
                file_key,
                expires_in,
            )

            download_url = self.info.get_download_url()

            return (
                f"{download_url}/file/"
                f"{self.bucket_name}/"
                f"{file_key}"
                f"?Authorization={authorization}"
            )

        except B2Error as e:

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

            file_versions = self.bucket.ls(
                file_key,
                latest_only=True,
            )

            for _, _ in file_versions:
                return True

            return False

        except B2Error:

            return False