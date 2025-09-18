# spaces_storage.py
import os
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import uuid
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DigitalOceanSpaces:
    def __init__(self):
        self.access_key = os.getenv("DO_SPACES_ACCESS_KEY")
        self.secret_key = os.getenv("DO_SPACES_SECRET_KEY")
        self.region = os.getenv("DO_SPACES_REGION", "sfo3")
        self.bucket_name = os.getenv("DO_SPACES_BUCKET", "lessonplanhygienequest")
        self.endpoint_url = f"https://{self.region}.digitaloceanspaces.com"

        if not self.access_key or not self.secret_key:
            raise ValueError("❌ DigitalOcean Spaces credentials not found in environment variables")

        try:
            self.s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
            )
            logger.info("✅ Connected to DigitalOcean Spaces successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize DigitalOcean Spaces client: {str(e)}")
            raise

    def upload_file(self, file_content, filename, content_type=None):
        """Upload an image to Digital Ocean Spaces (public)"""
        try:
            file_extension = os.path.splitext(filename)[1].lower()

            # Allow common image formats
            allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".svg"}
            if file_extension not in allowed_extensions:
                return {"success": False, "error": f"File type '{file_extension}' not allowed"}

            # Organize by date
            date_path = datetime.utcnow().strftime("%Y/%m/%d")
            unique_filename = f"lesson_plans/{date_path}/{uuid.uuid4()}{file_extension}"

            # Upload with public-read ACL
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_filename,
                Body=file_content,
                ContentType=content_type or "application/octet-stream",
                ACL="public-read",
            )

            public_url = f"https://{self.bucket_name}.{self.region}.digitaloceanspaces.com/{unique_filename}"
            logger.info(f"✅ Uploaded file '{filename}' → {public_url}")

            return {
                "success": True,
                "file_path": unique_filename,
                "public_url": public_url,
                "filename": filename,
            }

        except NoCredentialsError:
            logger.error("❌ Upload failed: Credentials not available")
            return {"success": False, "error": "Credentials not available"}
        except ClientError as e:
            logger.error(f"❌ Upload failed: {str(e)}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ Unexpected error during upload: {str(e)}")
            return {"success": False, "error": str(e)}

    def generate_presigned_url(self, file_path, expiration_hours=1):
        """Generate a presigned URL for temporary access (optional if public)"""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_path},
                ExpiresIn=expiration_hours * 3600,
            )
            return url
        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {str(e)}")
            return None

    def delete_file(self, file_path):
        """Delete a file from Digital Ocean Spaces"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            logger.info(f"🗑️ Deleted file {file_path}")
            return True
        except ClientError as e:
            logger.error(f"❌ Failed to delete file {file_path}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error deleting file {file_path}: {str(e)}")
            return False


# Singleton instance
do_spaces = DigitalOceanSpaces()
