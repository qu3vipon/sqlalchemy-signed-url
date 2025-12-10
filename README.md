# sqlalchemy-signed-url

`sqlalchemy-signed-url` is a small utility library that helps you work with  
**private object storage (S3, GCS, etc.) at the SQLAlchemy field level**.

The core idea is simple:

- **Store only object keys in the database**
- **Generate signed URLs (presigned URLs) only at read/serialization time**
- Keep upload and write operations **explicit and outside the ORM**

This library provides a clean, repeatable pattern for doing exactly that.

---

## Motivation

In systems that use private object storage, the following pattern is very common:

- Files live in a **private bucket/container**
- The database stores a **key**, not a public URL
- Clients receive a **short-lived signed URL** when data is returned
- Upload and download logic is handled explicitly in the application layer

In practice, this logic often ends up:

- Scattered across serializers and service layers, or
- Reimplemented slightly differently for each model

Over time, this makes consistency and maintenance difficult.

`sqlalchemy-signed-url` moves this pattern to the **model field level**,  
so it can be declared once and reused everywhere.

---

## Core Idea

```python
class User(Base):
    profile_image_key = SignedURLField(
        base_path="users/profile",
        ttl=600,
    )
