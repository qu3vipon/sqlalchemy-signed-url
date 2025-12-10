from __future__ import annotations

from typing import Protocol


class URLSigner(Protocol):
    def scheme(self) -> str:
        """Return storage scheme (e.g. 's3', 'gs', 'azure')."""
        ...

    def generate(self, *, bucket: str, key: str, ttl: int) -> str:
        ...


class StorageConfig:
    """
    Global storage configuration.

    - Configure once at application startup.
    - Class-level configuration.
    """

    _storage_name: str | None = None
    _signer: URLSigner | None = None

    @classmethod
    def configure(cls, *, storage_name: str, signer: URLSigner) -> None:
        if not storage_name:
            raise ValueError("storage_name must be provided")
        if signer is None:
            raise ValueError("signer must be provided")

        cls._storage_name = storage_name.rstrip("/")
        cls._signer = signer

    @classmethod
    def get_signer(cls) -> URLSigner:
        return cls._signer

    @classmethod
    def build_uri(cls, object_path: str) -> str:
        object_path = object_path.lstrip("/")
        signer = cls.get_signer()
        return f"{signer.scheme()}://{cls._storage_name}/{object_path}"

    @classmethod
    def parse_uri(cls, uri: str) -> tuple[str, str]:
        if not uri:
            raise ValueError("Empty storage URI")

        if "://" not in uri:
            raise ValueError(f"Invalid storage URI: {uri}")

        scheme, rest = uri.split("://", 1)

        signer = cls.get_signer()
        if signer.scheme() != scheme:
            raise ValueError(
                f"Configured signer does not support scheme '{scheme}'"
            )

        if "/" not in rest:
            raise ValueError(f"Invalid storage URI: {uri}")

        bucket, key = rest.split("/", 1)

        if not (bucket and key):
            raise ValueError(f"Invalid storage URI: {uri}")

        return bucket, key
