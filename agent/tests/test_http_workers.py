"""
Test HTTP Workers - FastAPI endpoint tests for all workers
Story: 2.10.1 - Worker HTTP Framework Migration
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job(job_id: str = "test-job-uuid") -> dict:
    """Return a minimal valid job dict for tests."""
    return {
        "id": job_id,
        "status": "pending",
        "content_type": "link",
        "platform": "youtube",
        "payload": {
            "From": "whatsapp:+1234567890",
            "Body": "https://example.com/test",
            "MessageSid": "SM123",
        },
    }


# ---------------------------------------------------------------------------
# Scraper Worker Tests
# ---------------------------------------------------------------------------

class TestScraperWorkerHTTP:
    @patch("scraper_worker.ScraperWorker")
    def test_process_job_success(self, MockWorkerClass):
        """POST /process returns 200 on success."""
        from scraper_worker import app, lifespan  # noqa: F401

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = _make_job()
        mock_worker.process_and_update.return_value = True

        with patch("scraper_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["job_id"] == "test-job-uuid"
        mock_worker.fetch_and_lock_specific_job.assert_called_once_with("test-job-uuid")
        mock_worker.process_and_update.assert_called_once()

    @patch("scraper_worker.ScraperWorker")
    def test_process_job_not_found(self, MockWorkerClass):
        """POST /process returns 404 when job is not pending."""
        from scraper_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = None

        with patch("scraper_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "missing-job"})

        assert response.status_code == 404

    @patch("scraper_worker.ScraperWorker")
    def test_process_job_processing_failure(self, MockWorkerClass):
        """POST /process returns 500 when processing fails."""
        from scraper_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = _make_job()
        mock_worker.process_and_update.return_value = False

        with patch("scraper_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 500

    def test_process_job_worker_not_initialised(self):
        """POST /process returns 503 when the singleton is not ready."""
        from scraper_worker import app

        with patch("scraper_worker._worker", None):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 503


# ---------------------------------------------------------------------------
# Video Worker Tests
# ---------------------------------------------------------------------------

class TestVideoWorkerHTTP:
    @patch("video_worker.VideoWorker")
    def test_process_job_success(self, MockWorkerClass):
        """POST /process returns 200 on success."""
        from video_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = _make_job()
        mock_worker.process_and_update.return_value = True

        with patch("video_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    @patch("video_worker.VideoWorker")
    def test_process_job_not_found(self, MockWorkerClass):
        """POST /process returns 404 when job not found."""
        from video_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = None

        with patch("video_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "ghost"})

        assert response.status_code == 404

    def test_process_job_worker_not_initialised(self):
        """POST /process returns 503 when singleton is not ready."""
        from video_worker import app

        with patch("video_worker._worker", None):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 503


# ---------------------------------------------------------------------------
# Image Worker Tests
# ---------------------------------------------------------------------------

class TestImageWorkerHTTP:
    @patch("image_worker.ImageWorker")
    def test_process_job_success(self, MockWorkerClass):
        """POST /process returns 200 on success."""
        from image_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = _make_job()
        mock_worker.process_and_update.return_value = True

        with patch("image_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    @patch("image_worker.ImageWorker")
    def test_process_job_not_found(self, MockWorkerClass):
        """POST /process returns 404 when job not found."""
        from image_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = None

        with patch("image_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "ghost"})

        assert response.status_code == 404

    def test_process_job_worker_not_initialised(self):
        """POST /process returns 503 when singleton is not ready."""
        from image_worker import app

        with patch("image_worker._worker", None):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 503


# ---------------------------------------------------------------------------
# Article Worker Tests
# ---------------------------------------------------------------------------

class TestArticleWorkerHTTP:
    @patch("article_worker.ArticleWorker")
    def test_process_job_success(self, MockWorkerClass):
        """POST /process returns 200 on success."""
        from article_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = _make_job()
        mock_worker.process_job.return_value = True

        with patch("article_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 200

    @patch("article_worker.ArticleWorker")
    def test_process_job_not_found(self, MockWorkerClass):
        """POST /process returns 404 when job not found."""
        from article_worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = None

        with patch("article_worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "ghost"})

        assert response.status_code == 404

    def test_process_job_worker_not_initialised(self):
        """POST /process returns 503 when singleton is not ready."""
        from article_worker import app

        with patch("article_worker._worker", None):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 503


# ---------------------------------------------------------------------------
# Classifier Worker Tests
# ---------------------------------------------------------------------------

class TestClassifierWorkerHTTP:
    @patch("worker.ClassifierWorker")
    def test_process_job_success(self, MockWorkerClass):
        """POST /process returns 200 on success."""
        from worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = _make_job()
        mock_worker.classify_and_update.return_value = True

        with patch("worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=True)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 200
        assert response.json()["status"] == "success"

    @patch("worker.ClassifierWorker")
    def test_process_job_not_found(self, MockWorkerClass):
        """POST /process returns 404 when job not found."""
        from worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = None

        with patch("worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "ghost"})

        assert response.status_code == 404

    @patch("worker.ClassifierWorker")
    def test_process_job_classify_failure(self, MockWorkerClass):
        """POST /process returns 500 when classification fails."""
        from worker import app

        mock_worker = MockWorkerClass.return_value
        mock_worker.fetch_and_lock_specific_job.return_value = _make_job()
        mock_worker.classify_and_update.return_value = False

        with patch("worker._worker", mock_worker):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 500

    def test_process_job_worker_not_initialised(self):
        """POST /process returns 503 when singleton is not ready."""
        from worker import app

        with patch("worker._worker", None):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": "test-job-uuid"})

        assert response.status_code == 503


# ---------------------------------------------------------------------------
# Input Validation Tests (all workers share same ProcessRequest schema)
# ---------------------------------------------------------------------------

class TestInputValidation:
    def test_empty_job_id_returns_422(self):
        """POST /process with empty job_id should return 422 (Field validation)."""
        from scraper_worker import app

        with patch("scraper_worker._worker", MagicMock()):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={"job_id": ""})

        assert response.status_code == 422

    def test_missing_job_id_returns_422(self):
        """POST /process with no job_id field returns 422."""
        from scraper_worker import app

        with patch("scraper_worker._worker", MagicMock()):
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post("/process", json={})

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Lifespan / Startup Failure Tests
# ---------------------------------------------------------------------------

class TestLifespanStartupFailure:
    def test_lifespan_propagates_worker_init_error(self):
        """If worker __init__ raises, the lifespan should propagate the error."""
        import scraper_worker

        original_worker_cls = scraper_worker.ScraperWorker
        try:
            with patch.object(
                scraper_worker,
                "ScraperWorker",
                side_effect=EnvironmentError("Missing env vars")
            ):
                # TestClient raises the startup exception when lifespan fails
                with pytest.raises(EnvironmentError, match="Missing env vars"):
                    with TestClient(scraper_worker.app):
                        pass
        finally:
            scraper_worker.ScraperWorker = original_worker_cls

