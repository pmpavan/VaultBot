import os
import pytest
from fastapi.testclient import TestClient
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

# We can test any worker, they all use the same security logic
# Let's test the Classifier Worker (worker.py)
from worker import app

client = TestClient(app)

@pytest.fixture
def mock_secret(monkeypatch):
    monkeypatch.setenv("WORKER_SECRET", "test-secret")
    return "test-secret"

def test_process_no_secret(mock_secret):
    """Test that a request with no secret is rejected with 401."""
    response = client.post("/process", json={"job_id": "test-uuid"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

def test_process_wrong_secret(mock_secret):
    """Test that a request with the wrong secret is rejected with 401."""
    response = client.post(
        "/process", 
        json={"job_id": "test-uuid"},
        headers={"X-VaultBot-Worker-Secret": "wrong-secret"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}

def test_process_correct_secret(mock_secret, monkeypatch):
    """Test that a request with the correct secret passes security."""
    from worker import ClassifierWorker
    import worker
    worker._worker = "mock-string" # Fake initialization
    
    # Passing the correct secret should result in an AttributeError 
    # because it tries to call a method on the string "mock-string"
    # This confirms that the 401 check was bypassed.
    with pytest.raises(AttributeError):
        client.post(
            "/process", 
            json={"job_id": "test-uuid"},
            headers={"X-VaultBot-Worker-Secret": "test-secret"}
        )
