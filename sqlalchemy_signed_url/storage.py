from __future__ import annotations

from typing import Protocol


class URLSigner(Protocol):
    @property
    def scheme(self) -> str:
        """Return storage scheme (e.g. 's3', 'gs', 'azure')."""
        ...

    @property
    def bucket(self) -> str: ...

    def sign(self, *, bucket: str, key: str, ttl: int) -> str: ...


class ObjectStorage:
    _signer: URLSigner | None = None

    @classmethod
    def initialize(cls, *, signer: URLSigner) -> None:
        cls._signer = signer

    @classmethod
    def build_uri(cls, *, key: str) -> str:
        """
        Build a new storage URI using signer defaults.

        NOTE:
        - This method is for *new objects only*.
        - The bucket used here comes from the signer configuration.
        - Existing data must NEVER rely on this method for signing.
        """
        return f"{cls._signer.scheme}://{cls._signer.bucket}/{key}"

    @classmethod
    def sign(cls, uri: str, *, ttl: int) -> str:
        """
        Generate a signed URL for the given full URI.

        NOTE:
        - URI is the source of truth.
          The bucket and key used for signing are ALWAYS derived from the URI itself.
        - The signer must NOT override or reinterpret the bucket.
          This ensures legacy objects remain valid even if the default bucket changes later.
        """
        _, bucket, key = cls._parse_uri(uri)
        return cls._signer.sign(bucket=bucket, key=key, ttl=ttl)

    @staticmethod
    def _parse_uri(uri: str) -> tuple[str, str, str]:
        try:
            scheme, rest = uri.split("://", 1)
        except ValueError:
            raise ValueError(f"invalid uri: {uri}")

        bucket, _, key = rest.partition("/")
        if not (bucket and key):
            raise ValueError(f"invalid uri: {uri}")

        return scheme, bucket, key

    @classmethod
    def parse_uri(cls, uri: str) -> tuple[str, str]:
        """
        Parse the given URI (scheme://bucket/key) and return (bucket, key).

        NOTE:
        URI is the source of truth.
        """
        _, bucket, key = cls._parse_uri(uri)
        return bucket, key
