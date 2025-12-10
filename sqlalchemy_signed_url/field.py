from __future__ import annotations

from typing import Annotated, Any

from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column

from .config import StorageConfig


class SignedURLField:
    """
    Contract:
    - Database column name is <field> (e.g. 'profile_image').
    - Internal ORM attribute is `_<field>_uri` (e.g. '_profile_image_uri').
    - Database stores the full storage URI (e.g. s3://bucket/path/key).
    - <field> exposes the full storage URI (read-only).
    - <field>_key exposes the raw key (read/write).
    - <field>_signed_url exposes the presigned URL (read-only).
    """

    def __init__(
        self,
        *,
        base_path: Annotated[str, "Base path inside the storage bucket"] = "",
        ttl: Annotated[int, "Signed URL TTL (seconds)"] = 300,
        length: Annotated[int, "DB column length"] = 512,
        nullable: Annotated[bool, "Whether the DB column is nullable"] = False,
    ):
        self.base_path = base_path.strip("/")
        self.ttl = ttl
        self.length = length
        self.nullable = nullable

    def __set_name__(self, owner: type[Any], name: str):
        internal_name = f"_{name}_uri"
        signed_url_cache_attr = f"_{name}_signed_url_cache"

        setattr(
            owner,
            internal_name,
            mapped_column(
                name,
                String(self.length),
                nullable=self.nullable,
            ),
        )

        def _build_uri_from_key(key: str | None) -> str | None:
            if key is None:
                return None

            if self.base_path:
                object_path = f"{self.base_path}/{key}"
            else:
                object_path = key

            return StorageConfig.build_uri(object_path)

        def _extract_key_from_uri(uri: str | None) -> str | None:
            if uri is None:
                return None
            return uri.rsplit("/", 1)[-1]

        def _validate_raw_key(key: str | None, field_name: str) -> None:
            if key is None:
                return

            if not isinstance(key, str):
                raise TypeError(f"{field_name}_key must be a string or None")

            if key == "":
                raise ValueError(f"{field_name}_key cannot be empty")

            if key.startswith("/"):
                raise ValueError(f"{field_name}_key must not start with '/'")

            if "://" in key:
                raise ValueError(f"{field_name}_key must not contain a URI scheme")

            if ".." in key:
                raise ValueError(f"{field_name}_key must not contain '..'")

            if key.strip() != key:
                raise ValueError(f"{field_name}_key cannot contain leading/trailing whitespace")

        # <field>(read-only)
        @hybrid_property
        def _storage_uri(obj) -> str | None:
            return getattr(obj, internal_name)

        @_storage_uri.setter
        def _storage_uri(obj, value):
            raise AttributeError(
                f"'{name}' is read-only. Assign a raw key via '{name}_key' instead."
            )

        setattr(owner, name, _storage_uri)

        # <field>_key
        @property
        def _key_accessor(obj) -> str | None:
            full_uri = getattr(obj, internal_name)
            return _extract_key_from_uri(full_uri)

        @_key_accessor.setter
        def _key_accessor(obj, raw_key: str | None) -> None:
            _validate_raw_key(raw_key, name)
            full_uri = _build_uri_from_key(raw_key)
            setattr(obj, internal_name, full_uri)

            if hasattr(obj, signed_url_cache_attr):
                delattr(obj, signed_url_cache_attr)

        setattr(owner, f"{name}_key", _key_accessor)

        # <field>_signed_url
        @property
        def _signed_url(obj) -> str | None:
            cached = getattr(obj, signed_url_cache_attr, None)
            if cached is not None:
                return cached

            full_uri = getattr(obj, internal_name)
            if full_uri is None:
                return None

            bucket, key = StorageConfig.parse_uri(full_uri)
            signer = StorageConfig.get_signer()
            signed = signer.generate(bucket=bucket, key=key, ttl=self.ttl)

            setattr(obj, signed_url_cache_attr, signed)
            return signed

        setattr(owner, f"{name}_signed_url", _signed_url)

        # <field>_location
        @property
        def _location(obj) -> tuple[str, str] | None:
            full_uri = getattr(obj, internal_name)
            if full_uri is None:
                return None

            bucket, key = StorageConfig.parse_uri(full_uri)
            return bucket, key

        setattr(owner, f"{name}_location", _location)
