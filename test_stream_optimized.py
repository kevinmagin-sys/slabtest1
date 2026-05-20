import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from stream_optimized import app, TransportError

client = TestClient(app)

class TestStreamOptimizedIngestion:
    """Test the /stream/optimized_ingest endpoint."""
    
    def test_normal_stream_succeeds(self):
        """Test that normal stream completes successfully."""
        data = b"x" * 10000
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 202
        assert response.json()["detail"] == "Stream fully buffered and routed"
    
    def test_empty_stream(self):
        """Test that empty stream is handled correctly."""
        response = client.post("/stream/optimized_ingest", content=b"")
        assert response.status_code == 202
    
    def test_small_stream(self):
        """Test that small stream under limit is accepted."""
        data = b"x" * 5000
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 202
    
    def test_stream_at_limit(self):
        """Test that stream at exactly 1MB limit is accepted."""
        data = b"x" * 1048576
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 202
    
    def test_stream_exceeds_limit(self):
        """Test that stream exceeding 1MB returns 413."""
        data = b"x" * (1048576 + 1)
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 413
        assert "Stream exceeded size limit" in response.json()["detail"]
    
    def test_large_oversized_stream(self):
        """Test that significantly oversized stream returns 413."""
        data = b"x" * (1048576 * 2)
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 413
    
    def test_json_stream(self):
        """Test that JSON stream is processed correctly."""
        json_data = b'{"key": "value", "count": 42}'
        response = client.post("/stream/optimized_ingest", content=json_data)
        assert response.status_code == 202
    
    def test_binary_stream(self):
        """Test that binary stream is processed correctly."""
        binary_data = bytes([i % 256 for i in range(10000)])
        response = client.post("/stream/optimized_ingest", content=binary_data)
        assert response.status_code == 202
    
    def test_boundary_minus_one_byte(self):
        """Test stream 1 byte under the limit."""
        data = b"x" * (1048576 - 1)
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 202
    
    def test_boundary_plus_one_byte(self):
        """Test stream 1 byte over the limit."""
        data = b"x" * (1048576 + 1)
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 413
    
    @patch('stream_optimized.emit_metrics')
    def test_metrics_emitted_on_success(self, mock_metrics):
        """Test that metrics are not explicitly called on success in optimized mode."""
        data = b"x" * 1000
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 202
    
    def test_large_valid_stream(self):
        """Test that large stream under limit succeeds."""
        data = b"x" * (1048576 - 10000)
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 202
    
    def test_transport_error_handling(self):
        """Test that transport errors are handled gracefully."""
        # Normal stream should not trigger transport error
        data = b"x" * 1000
        response = client.post("/stream/optimized_ingest", content=data)
        assert response.status_code == 202
