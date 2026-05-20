import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pipeline import app, SlabPayload, QueueError

client = TestClient(app)

class TestPipelineIngestion:
    """Test the /pipeline/ingest endpoint."""
    
    def test_valid_ingestion_request(self):
        """Test successful ingestion with valid payload."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {"key": "value", "number": 42}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 202
        assert response.json()["detail"] == "Accepted for processing"
    
    def test_content_length_header_too_large(self):
        """Test that Content-Length header exceeding limit returns 413."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {"key": "value"}
        }
        # Manually set an oversized Content-Length header
        headers = {"content-length": str(1048576 + 1000)}
        response = client.post("/pipeline/ingest", json=payload, headers=headers)
        assert response.status_code == 413
        assert "Payload size exceeded limit" in response.json()["detail"]
    
    def test_invalid_json_payload(self):
        """Test that malformed JSON returns 400."""
        response = client.post(
            "/pipeline/ingest",
            content="{invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 400
        assert "Invalid JSON format" in response.json()["detail"]
    
    def test_missing_identifier_field(self):
        """Test that missing identifier returns 422."""
        test_time = datetime.now().isoformat()
        payload = {
            "timestamp": test_time,
            "payload_data": {"key": "value"}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_missing_timestamp_field(self):
        """Test that missing timestamp returns 422."""
        test_id = str(uuid.uuid4())
        payload = {
            "identifier": test_id,
            "payload_data": {"key": "value"}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_missing_payload_data_field(self):
        """Test that missing payload_data returns 422."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_invalid_identifier_format(self):
        """Test that invalid UUID identifier returns 422."""
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": "not-a-uuid",
            "timestamp": test_time,
            "payload_data": {"key": "value"}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_invalid_timestamp_format(self):
        """Test that invalid timestamp returns 422."""
        test_id = str(uuid.uuid4())
        payload = {
            "identifier": test_id,
            "timestamp": "not-a-timestamp",
            "payload_data": {"key": "value"}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_extra_fields_rejected(self):
        """Test that extra fields are rejected."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {"key": "value"},
            "extra_field": "should_fail"
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_queue_error_returns_503(self):
        """Test that QueueError returns 503 Service Unavailable."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {"key": "value"}
        }
        with patch('pipeline.push_to_downstream_queue') as mock_queue:
            mock_queue.side_effect = QueueError("Queue unavailable")
            response = client.post("/pipeline/ingest", json=payload)
            assert response.status_code == 503
            assert "Service Unavailable" in response.json()["detail"]
    
    def test_nested_payload_data(self):
        """Test that nested JSON structures are accepted."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {
                "level1": {
                    "level2": {
                        "level3": [1, 2, 3, {"key": "value"}]
                    }
                },
                "array": ["a", "b", "c"]
            }
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 202
        assert response.json()["detail"] == "Accepted for processing"
    
    def test_empty_payload_data(self):
        """Test that empty payload_data dict is accepted."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 202
        assert response.json()["detail"] == "Accepted for processing"
    
    @patch('pipeline.emit_metrics')
    def test_metrics_emitted_on_success(self, mock_metrics):
        """Test that metrics are emitted on successful ingestion."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {"key": "value"}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 202
        mock_metrics.assert_called_once()
        call_args = mock_metrics.call_args
        assert call_args[1]["type"] == "ingestion_success"
    
    @patch('pipeline.emit_metrics')
    def test_metrics_emitted_on_schema_failure(self, mock_metrics):
        """Test that metrics are emitted on schema validation failure."""
        test_time = datetime.now().isoformat()
        payload = {
            "timestamp": test_time,
            "payload_data": {"key": "value"}
        }
        response = client.post("/pipeline/ingest", json=payload)
        assert response.status_code == 422
        mock_metrics.assert_called_once()
        call_args = mock_metrics.call_args
        assert call_args[1]["type"] == "ingestion_failure"
