# sqlalchemy-signed-url

`sqlalchemy-signed-url` is a small utility library that helps you work with **private object storage (S3, GCS, etc.) at the SQLAlchemy field level**.

The core idea is simple:

- **Store only object keys in the database**
- **Generate signed URLs (presigned URLs) only at read/serialization time**
- Keep upload and write operations **explicit and outside the ORM**

This library provides a clean, repeatable pattern for doing exactly that.

## Motivation

In systems that use private object storage, the following pattern is very common:

- Files live in a **private bucket/container**
- The database stores a full storage URI, not a public-facing URL.
- Clients receive a **short-lived signed URL** when data is returned
- Upload and download logic is handled explicitly in the application layer

In practice, this logic often ends up:

- Scattered across serializers and service layers, or
- Reimplemented slightly differently for each model

Over time, this makes consistency and maintenance difficult.

`sqlalchemy-signed-url` moves this pattern to the **model field level**, so it can be declared once and reused everywhere.

## Example

### 1. Configure storage (once)
```python
from sqlalchemy_signed_url import ObjectStorage
from sqlalchemy_signed_url.signers.s3 import S3PresignedURLSigner

ObjectStorage.initialize(
    signer=S3PresignedURLSigner(bucket="my-bucket", region_name="us-east-1"),
)
```
### 2. Declare a model
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_signed_url import SignedURLField


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_image = SignedURLField(base_path="users/profile")
```

### 3. Save (assign raw key)
```python
# The field automatically provides:
# - <field>_key        → raw key accessor
# - <field>_location   → (bucket, object_key) for uploading
# - <field>_signed_url → on-demand presigned URL

# Assign a raw key to the model (no upload yet)
user = User(profile_image_key="avatar.png")

# Get upload destination from the model
bucket, key = user.profile_image_location

# Upload the file yourself
s3_client.upload_file("local/path/avatar.png", bucket, key)

# Save the key to the database
session.add(user)
session.commit()
```

### 4. Read
```python
user.profile_image
# "s3://my-bucket/users/profile/avatar.png"

user.profile_image_key
# "avatar.png"

user.profile_image_signed_url
# presigned URL
```

## Status
### ✅ Implemented
- [x] S3-based presigned URL generation (read-only)
- [x] Instance-level caching of presigned URLs
  - [x] Cache per ORM instance
  - [x] Invalidate cache when `<field>_key` changes
- [x] Allow injecting storage client

### 🚧 Planned
- [ ] Support additional storage providers
  - [ ] Google Cloud Storage (GCS)
  - [ ] Microsoft Azure Blob Storage
  - [ ] Other S3-compatible storages

- [ ] Presigned URL for uploads
  - [ ] Generate upload URLs (e.g. `PUT`, `POST`)
  - [ ] Separate read/write URL configuration
  - [ ] Optional constraints (content-type, max size, etc.)

- [ ] Validate Alembic compatibility
  - [ ] Confirm autogenerate behavior with `SignedURLField`
