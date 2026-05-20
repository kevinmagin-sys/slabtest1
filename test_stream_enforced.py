import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from stream_enforced import app

client = TestClient(app)

class TestStreamInfrastructureEnforced:
    """Test the /stream/enforced endpoint with infrastructure-level protections."""
    
    def test_valid_stream_accepted(self):
        """Test that valid stream is accepted."""
        data = b"test data"
        response = client.post("/stream/enforced", content=data)
        assert response.status_code == 202
        assert response.json()["detail"] == "Accepted"
    
    def test_empty_stream_accepted(self):
        """Test that empty stream is handled."""
        response = client.post("/stream/enforced", content=b"")
        assert response.status_code == 202
    
    def test_json_stream_accepted(self):
        """Test that JSON stream is accepted."""
        json_data = b'{"key": "value"}'
        response = client.post("/stream/enforced", content=json_data)
        assert response.status_code == 202
    
    def test_large_valid_stream(self):
        """Test that large valid stream is accepted."""
        large_data = b"x" * 100000
        response = client.post("/stream/enforced", content=large_data)
        assert response.status_code == 202
    
    def test_binary_stream_accepted(self):
        """Test that binary stream is accepted."""
        binary_data = bytes([i % 256 for i in range(5000)])
        response = client.post("/stream/enforced", content=binary_data)
        assert response.status_code == 202
    
    @patch('stream_enforced.route_to_schema_validation')
    def test_schema_validation_called(self, mock_validation):
        """Test that schema validation is called with buffer."""
        data = b"test data"
        response = client.post("/stream/enforced", content=data)
        assert response.status_code == 202
        mock_validation.assert_called_once_with(data)
    
    @patch('stream_enforced.route_to_schema_validation')
    def test_schema_validation_failure_returns_422(self, mock_validation):
        """Test that schema validation failure returns 422."""
        mock_validation.side_effect = Exception("Schema validation failed")
        data = b"test data"
        response = client.post("/stream/enforced", content=data)
        assert response.status_code == 422
        assert "Invalid Data" in response.json()["detail"]
    
    @patch('stream_enforced.emit_metrics')
    @patch('stream_enforced.route_to_schema_validation')
    def test_metrics_emitted_on_schema_failure(self, mock_validation, mock_metrics):
        """Test that metrics are emitted on schema validation failure."""
        mock_validation.side_effect = Exception("Validation failed")
        data = b"test data"
        response = client.post("/stream/enforced", content=data)
        assert response.status_code == 422
        mock_metrics.assert_called_once_with(type="schema_violation")
    
    @patch('stream_enforced.emit_metrics')
    def test_metrics_emitted_on_success(self, mock_metrics):
        """Test that metrics are emitted on successful validation."""
        data = b"test data"
        response = client.post("/stream/enforced", content=data)
        assert response.status_code == 202
        mock_metrics.assert_called_once_with(type="ingestion_success")
    
    def test_infrastructure_enforced_assumptions(self):
        """Test that endpoint assumes infrastructure handles size/timeout limits."""
        # This endpoint assumes infrastructure (reverse proxy, load balancer) 
        # has already enforced size and timeout limits before the request reaches here
        data = b"x" * 50000
        response = client.post("/stream/enforced", content=data)
        # Should succeed because infrastructure is assumed to have validated
        assert response.status_code == 202
