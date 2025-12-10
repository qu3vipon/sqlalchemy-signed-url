from __future__ import annotations

import re
from typing import Optional

import boto3


class S3PresignedURLSigner:
    """
    Boto3-based S3 presigned URL signer.
    """

    def __init__(
        self,
        *,
        region_name: Optional[str] = None,
        client_kwargs: Optional[dict] = None,
    ):
        self._client = boto3.client(
            "s3",
            region_name=region_name,
            **(client_kwargs or {}),
        )

    def scheme(self) -> str:
        return "s3"

    def generate(self, *, bucket: str, key: str, ttl: int) -> str:
        return self._client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=ttl,
        )
