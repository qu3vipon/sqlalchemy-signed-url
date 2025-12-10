import pytest
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from sqlalchemy_signed_url import ObjectStorage, SignedURLField


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_image = SignedURLField(base_path="users/profile", ttl=600)


def test_storage_config_and_field_behavior(mock_signer):
    ObjectStorage.initialize(signer=mock_signer)

    u = User(profile_image_key="abc.png")
    assert u.profile_image == "mock://my-bucket/users/profile/abc.png"

    assert u.profile_image_location == ("my-bucket", "users/profile/abc.png")

    with pytest.raises(AttributeError, match="read-only"):
        u.profile_image = "anything"

    assert u.profile_image_key == "abc.png"

    signed = u.profile_image_signed_url
    assert signed == "signed://my-bucket/users/profile/abc.png?ttl=600"
    assert mock_signer.calls == [("my-bucket", "users/profile/abc.png", 600)]


def test_signed_url_is_cached(mock_signer):
    ObjectStorage.initialize(signer=mock_signer)

    u = User(profile_image_key="abc.png")

    url1 = u.profile_image_signed_url
    url2 = u.profile_image_signed_url

    assert url1 == url2
    assert mock_signer.calls == [("my-bucket", "users/profile/abc.png", 600)]


def test_signed_url_cache_invalidated_on_key_change(mock_signer):
    ObjectStorage.initialize(signer=mock_signer)

    u = User(profile_image_key="a.png")
    url1 = u.profile_image_signed_url

    u.profile_image_key = "b.png"
    url2 = u.profile_image_signed_url

    assert url1 != url2
    assert mock_signer.calls == [
        ("my-bucket", "users/profile/a.png", 600),
        ("my-bucket", "users/profile/b.png", 600),
    ]


def test_base_path_join(mock_signer):
    ObjectStorage.initialize(signer=mock_signer)

    u = User(profile_image_key="abc.png")

    # no double slashes
    assert u.profile_image == "mock://my-bucket/users/profile/abc.png"


def test_empty_base_path(mock_signer):
    class User2(Base):
        __tablename__ = "users2"
        id: Mapped[int] = mapped_column(primary_key=True)
        image = SignedURLField()

    ObjectStorage.initialize(signer=mock_signer)

    u = User2(image_key="a.png")
    assert u.image == "mock://my-bucket/a.png"


def test_none_key_clears_value_and_signed_url(mock_signer):
    ObjectStorage.initialize(signer=mock_signer)

    u = User(profile_image_key="a.png")
    _ = u.profile_image_signed_url

    u.profile_image_key = None

    assert u.profile_image is None
    assert u.profile_image_signed_url is None
    assert mock_signer.calls == [("my-bucket", "users/profile/a.png", 600)]


def test_multiple_fields_are_independent(mock_signer):
    class User3(Base):
        __tablename__ = "users3"
        id: Mapped[int] = mapped_column(primary_key=True)
        img1 = SignedURLField(base_path="a")
        img2 = SignedURLField(base_path="b")

    ObjectStorage.initialize(signer=mock_signer)

    u = User3()
    u.img1_key = "x.png"
    u.img2_key = "y.png"

    assert u.img1 == "mock://my-bucket/a/x.png"
    assert u.img2 == "mock://my-bucket/b/y.png"


def test_location_property(mock_signer):
    ObjectStorage.initialize(signer=mock_signer)

    u = User(profile_image_key="avatar.png")

    location = u.profile_image_location
    assert location == ("my-bucket", "users/profile/avatar.png")


def test_location_is_none_when_key_is_missing(mock_signer):
    ObjectStorage.initialize(signer=mock_signer)

    u = User()
    assert u.profile_image_location is None


def test_invalid_key():
    u = User()

    with pytest.raises(ValueError):
        u.profile_image_key = "/bad.png"

    with pytest.raises(ValueError):
        u.profile_image_key = "s3://evil"

    with pytest.raises(ValueError):
        u.profile_image_key = "../escape"

    with pytest.raises(ValueError):
        u.profile_image_key = "  bad.png  "
