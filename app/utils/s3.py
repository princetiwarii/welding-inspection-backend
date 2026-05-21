import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, UploadFile
from app.core.config import settings
import uuid
import os

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


def upload_file_to_s3(file_bytes: bytes, s3_key: str, content_type: str) -> str:
    """Upload bytes to S3 and return the public URL."""
    try:
        s3_client.put_object(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return f"{settings.AWS_S3_BASE_URL}/{s3_key}"
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {str(e)}")


async def upload_upload_file(upload_file: UploadFile, prefix: str) -> dict:
    """Upload a FastAPI UploadFile to S3. Returns s3_key and s3_url."""
    file_bytes = await upload_file.read()
    ext = os.path.splitext(upload_file.filename)[1] or ".bin"
    s3_key = f"{prefix}/{uuid.uuid4().hex}{ext}"
    content_type = upload_file.content_type or "application/octet-stream"
    s3_url = upload_file_to_s3(file_bytes, s3_key, content_type)
    return {
        "s3_key": s3_key,
        "s3_url": s3_url,
        "file_name": upload_file.filename,
        "file_size_bytes": len(file_bytes),
        "mime_type": content_type,
    }


def generate_presigned_url(s3_key: str, expires_in: int = 3600) -> str:
    """Generate a temporary presigned URL for private S3 objects."""
    try:
        return s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.AWS_S3_BUCKET_NAME, "Key": s3_key},
            ExpiresIn=expires_in,
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Presigned URL error: {str(e)}")


def delete_s3_object(s3_key: str):
    try:
        s3_client.delete_object(Bucket=settings.AWS_S3_BUCKET_NAME, Key=s3_key)
    except ClientError:
        pass  # Log and continue
