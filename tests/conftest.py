import pytest


class MockSigner:
    def __init__(self):
        self.calls = []

    @property
    def scheme(self):
        return "mock"

    @property
    def bucket(self) -> str:
        return "my-bucket"

    def sign(self, bucket: str, key: str, *, ttl: int) -> str:
        self.calls.append((bucket, key, ttl))
        return f"signed://{bucket}/{key}?ttl={ttl}"


@pytest.fixture
def mock_signer():
    return MockSigner()
