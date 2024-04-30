import json
import io
from urllib.parse import urljoin

import boto3
from django.conf import settings


class S3FileStorage:
    def __init__(self):
        self.session = boto3.session.Session()
        self.client = self.session.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
            region_name="us-east-1",
        )

    def buckets(self):
        return [item["Name"] for item in self.client.list_buckets()["Buckets"]]

    def create_bucket(self, name, public=False):
        self.client.create_bucket(Bucket=name)
        if public:
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{name}/*"
                    }
                ]
            }
            self.client.put_bucket_policy(Bucket=name, Policy=json.dumps(policy))

    def upload_file(self, fobj, bucket, filename, content_type=None):
        args = {}
        if content_type:
            args["ContentType"] = content_type
        self.client.upload_fileobj(Fileobj=fobj, Bucket=bucket, Key=filename, ExtraArgs=args)
        # TODO: should check result?
        if settings.AWS_S3_CUSTOM_DOMAIN:
            base_url = f"{settings.AWS_S3_URL_PROTOCOL}//{settings.AWS_S3_CUSTOM_DOMAIN}/"
        else:
            base_url = settings.AWS_S3_ENDPOINT_URL
        return urljoin(base_url, f"{bucket}/{filename}")

    def remote_copy(self, source_bucket, source_filename, destination_filename, destination_bucket=None):
        """Copy a file to another S3 location (to the same bucket or another)"""
        return self.client.copy(
            CopySource={"Bucket": source_bucket, "Key": source_filename},
            Bucket=destination_bucket if destination_bucket is not None else source_bucket,
            Key=destination_filename,
        )

    def delete(self, bucket, filename):
        """Delete a file from a bucket"""
        return self.client.delete_object(Bucket=bucket, Key=filename)


storage = S3FileStorage()
# Sample usage:
# fobj = io.BytesIO(b"hello, world!\r\n")
# storage.upload_file(fobj, "some-bucket", "hello.txt", content_type="text/plain")
