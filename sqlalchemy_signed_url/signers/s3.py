from __future__ import annotations

import boto3


class S3PresignedURLSigner:
    def __init__(
        self,
        *,
        region_name: str,
        bucket: str,
    ):
        self._region_name = region_name
        self._bucket = bucket
        self._client = boto3.client("s3", region_name=region_name)

    @property
    def bucket(self) -> str:
        return self._bucket

    @property
    def scheme(self) -> str:
        return "s3"

    def sign(self, *, bucket: str, key: str, ttl: int) -> str:
        """
        Generate a presigned URL for reading an object.

        Args:
            bucket: The S3 bucket name.
            key: object key in the bucket
            ttl: expiration in seconds

        Returns:
            str: fully signed URL
        """

        return self._client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
            },
            ExpiresIn=ttl,
        )
