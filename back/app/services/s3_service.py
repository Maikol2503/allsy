import boto3
import uuid
from fastapi import UploadFile
from app.core.config import settings

s3_client = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

def upload_image_to_s3(file: UploadFile, folder: str) -> str:
    extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    key = f"{folder}/{filename}"

    s3_client.upload_fileobj(
        file.file,
        settings.AWS_BUCKET_NAME,
        key,
        ExtraArgs={
            "ContentType": file.content_type
        }
    )

    return f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"




def delete_image_from_s3(url: str):
    """
    Elimina una imagen de S3 a partir de su URL pública.
    """
    bucket_name = settings.AWS_BUCKET_NAME
    region = settings.AWS_REGION

    # Obtener la "key" de la URL
    prefix = f"https://{bucket_name}.s3.{region}.amazonaws.com/"
    if url.startswith(prefix):
        key = url[len(prefix):]
        s3_client.delete_object(Bucket=bucket_name, Key=key)




