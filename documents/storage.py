import hashlib
from datetime import timedelta
from urllib.parse import urlparse

from django.conf import settings

try:
    from minio import Minio
    from minio.error import S3Error
except ModuleNotFoundError:  # pragma: no cover
    Minio = None
    S3Error = Exception


class _HashingReader:
    def __init__(self, fileobj):
        self.fileobj = fileobj
        self.hasher = hashlib.sha256()
        self.total_read = 0

    def read(self, size=-1):
        chunk = self.fileobj.read(size)
        if chunk:
            self.hasher.update(chunk)
            self.total_read += len(chunk)
        return chunk


def _endpoint_and_secure(raw_endpoint, default_secure):
    if not raw_endpoint:
        return "", default_secure

    endpoint = raw_endpoint.strip()
    secure = default_secure
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        parsed = urlparse(endpoint)
        endpoint = parsed.netloc
        secure = parsed.scheme == "https"
    return endpoint, secure


class DocumentsStorageClient:
    def __init__(self):
        if Minio is None:
            raise RuntimeError("The 'minio' package is required for document storage operations.")

        internal_endpoint, internal_secure = _endpoint_and_secure(
            settings.MINIO_ENDPOINT,
            settings.MINIO_USE_SSL,
        )
        public_endpoint, public_secure = _endpoint_and_secure(
            settings.MINIO_PUBLIC_ENDPOINT,
            settings.MINIO_PUBLIC_USE_SSL,
        )
        region = settings.MINIO_REGION or "us-east-1"

        self.client = Minio(
            internal_endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=internal_secure,
            region=region,
        )
        self.presign_client = Minio(
            public_endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=public_secure,
            region=region,
        )

    def ensure_bucket(self, bucket):
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
        except S3Error:
            # A concurrent create can race; verify again before surfacing.
            if not self.client.bucket_exists(bucket):
                raise

    def upload_fileobj(self, fileobj, bucket, object_key, content_type):
        self.ensure_bucket(bucket)

        fileobj.seek(0)
        reader = _HashingReader(fileobj)
        size = getattr(fileobj, "size", None)
        if size is None:
            current = fileobj.tell()
            fileobj.seek(0, 2)
            size = fileobj.tell()
            fileobj.seek(current)

        self.client.put_object(
            bucket,
            object_key,
            data=reader,
            length=size,
            content_type=content_type or "application/octet-stream",
        )

        return reader.total_read, reader.hasher.hexdigest()

    def presign_get(self, bucket, object_key, expires_seconds=None):
        expires = expires_seconds or settings.MINIO_PRESIGN_EXPIRES
        return self.presign_client.presigned_get_object(
            bucket,
            object_key,
            expires=timedelta(seconds=expires),
        )


def get_documents_storage_client():
    return DocumentsStorageClient()
