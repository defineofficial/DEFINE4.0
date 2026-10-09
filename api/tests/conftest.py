import pytest


@pytest.fixture(autouse=True)
def mock_mode_by_default(request, monkeypatch):
    """Most tests run in mock mode, even when .env sets DATABASE_URL.

    Tests marked `database` set it themselves from TEST_DATABASE_URL.
    """
    if "database" not in request.keywords:
        monkeypatch.delenv("DATABASE_URL", raising=False)
