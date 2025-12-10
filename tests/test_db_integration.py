from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from sqlalchemy_signed_url import SignedURLField, StorageConfig


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_image = SignedURLField(base_path="users/profile", ttl=600)


def test_db_integration_round_trip(mock_signer):
    StorageConfig.configure(storage_name="my-bucket", signer=mock_signer)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        u = User(profile_image_key="abc.png")
        session.add(u)
        session.commit()
        user_id = u.id

    with Session(engine) as session:
        u = session.get(User, user_id)

        assert u.profile_image == "mock://my-bucket/users/profile/abc.png"
