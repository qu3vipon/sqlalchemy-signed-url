import pytest


class MockSigner:
    def __init__(self):
        self.calls = []

    def scheme(self):
        return "mock"

    def generate(self, bucket: str, key: str, *, ttl: int) -> str:
        self.calls.append((bucket, key, ttl))
        return f"signed://{bucket}/{key}?ttl={ttl}"


@pytest.fixture
def mock_signer():
    return MockSigner()
