import pytest
import uuid
from datetime import datetime
from fastapi.testclient import TestClient
from app import app, SlabPayload

client = TestClient(app)

class TestSlabPayloadSchema:
    """Test the SlabPayload schema validation."""
    
    def test_valid_payload_creation(self):
        """Test creating a valid SlabPayload."""
        test_id = uuid.uuid4()
        test_time = datetime.now()
        payload = SlabPayload(
            identifier=test_id,
            timestamp=test_time,
            payload_data={"key": "value", "nested": {"data": 123}}
        )
        assert payload.identifier == test_id
        assert payload.timestamp == test_time
        assert payload.payload_data["key"] == "value"
    
    def test_missing_required_field_identifier(self):
        """Test that missing identifier raises ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SlabPayload(
                timestamp=datetime.now(),
                payload_data={"key": "value"}
            )
    
    def test_missing_required_field_timestamp(self):
        """Test that missing timestamp raises ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SlabPayload(
                identifier=uuid.uuid4(),
                payload_data={"key": "value"}
            )
    
    def test_missing_required_field_payload_data(self):
        """Test that missing payload_data raises ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SlabPayload(
                identifier=uuid.uuid4(),
                timestamp=datetime.now()
            )
    
    def test_rejects_unknown_fields(self):
        """Test that extra fields are rejected."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SlabPayload(
                identifier=uuid.uuid4(),
                timestamp=datetime.now(),
                payload_data={"key": "value"},
                extra_field="should_fail"
            )
    
    def test_invalid_identifier_format(self):
        """Test that invalid UUID format is rejected."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SlabPayload(
                identifier="not-a-uuid",
                timestamp=datetime.now(),
                payload_data={"key": "value"}
            )
    
    def test_invalid_timestamp_format(self):
        """Test that invalid datetime format is rejected."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SlabPayload(
                identifier=uuid.uuid4(),
                timestamp="not-a-datetime",
                payload_data={"key": "value"}
            )


class TestIngestionBoundaryEndpoint:
    """Test the /ingest endpoint."""
    
    def test_valid_ingestion_request(self):
        """Test successful ingestion with valid payload."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {"key": "value", "number": 42}
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 202
        assert response.json()["detail"] == "Accepted for processing"
    
    def test_invalid_json_payload(self):
        """Test that malformed JSON returns 422."""
        response = client.post(
            "/ingest",
            content="{invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
        assert "Invalid JSON" in response.json()["detail"]
    
    def test_missing_identifier_field(self):
        """Test that missing identifier returns 422."""
        test_time = datetime.now().isoformat()
        payload = {
            "timestamp": test_time,
            "payload_data": {"key": "value"}
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_missing_timestamp_field(self):
        """Test that missing timestamp returns 422."""
        test_id = str(uuid.uuid4())
        payload = {
            "identifier": test_id,
            "payload_data": {"key": "value"}
        }
        response = client.post("/ingest", json=payload)
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
        response = client.post("/ingest", json=payload)
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
        response = client.post("/ingest", json=payload)
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
        response = client.post("/ingest", json=payload)
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
        response = client.post("/ingest", json=payload)
        assert response.status_code == 422
        assert "detail" in response.json()
    
    def test_payload_too_large(self):
        """Test that oversized payload returns 413."""
        test_id = str(uuid.uuid4())
        test_time = datetime.now().isoformat()
        # Create payload larger than 1MB
        large_data = "x" * (1048576 + 1000)  # 1MB + 1000 bytes
        payload = {
            "identifier": test_id,
            "timestamp": test_time,
            "payload_data": {"large_field": large_data}
        }
        response = client.post("/ingest", json=payload)
        assert response.status_code == 413
        assert "Payload size exceeded limit" in response.json()["detail"]
    
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
        response = client.post("/ingest", json=payload)
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
        response = client.post("/ingest", json=payload)
        assert response.status_code == 202
        assert response.json()["detail"] == "Accepted for processing"
