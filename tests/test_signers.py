from sqlalchemy_signed_url.signers.s3 import S3PresignedURLSigner


class FakeS3Client:
    @staticmethod
    def generate_presigned_url(*args, **kwargs):
        return "signed-url"

def test_signer_uses_given_client(monkeypatch):
    fake_client = FakeS3Client()
    signer = S3PresignedURLSigner(
        bucket="my-bucket",
        region_name="us-east-1",
        client=fake_client,
    )

    def fail_client(*args, **kwargs):
        raise AssertionError("boto3.client should not be called")

    monkeypatch.setattr("boto3.client", fail_client)

    url = signer.sign(bucket="any", key="test.png", ttl=60)
    assert url == "signed-url"
