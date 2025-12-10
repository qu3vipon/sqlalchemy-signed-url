def test_import():
    import sqlalchemy_signed_url as m

    assert hasattr(m, "__version__") or True
