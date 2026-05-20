import pytest
from fastapi.testclient import TestClient
from stream import app

client = TestClient(app)

class TestStreamBoundary:
    """Test the /stream/ingest endpoint."""
    
    def test_empty_stream(self):
        """Test that empty stream is accepted."""
        response = client.post("/stream/ingest", content=b"")
        assert response.status_code == 202
        assert response.json()["detail"] == "Stream fully buffered and routed"
    
    def test_small_stream(self):
        """Test that small stream under limit is accepted."""
        small_data = b"x" * 1000  # 1KB
        response = client.post("/stream/ingest", content=small_data)
        assert response.status_code == 202
        assert response.json()["detail"] == "Stream fully buffered and routed"
    
    def test_stream_at_limit(self):
        """Test that stream at exactly the 1MB limit is accepted."""
        limit_data = b"x" * 1048576  # Exactly 1MB
        response = client.post("/stream/ingest", content=limit_data)
        assert response.status_code == 202
        assert response.json()["detail"] == "Stream fully buffered and routed"
    
    def test_stream_exceeds_limit(self):
        """Test that stream exceeding 1MB returns 413."""
        oversized_data = b"x" * (1048576 + 1)  # 1MB + 1 byte
        response = client.post("/stream/ingest", content=oversized_data)
        assert response.status_code == 413
        assert "Stream exceeded size limit" in response.json()["detail"]
    
    def test_stream_significantly_oversized(self):
        """Test that significantly oversized stream returns 413."""
        oversized_data = b"x" * (1048576 * 2)  # 2MB
        response = client.post("/stream/ingest", content=oversized_data)
        assert response.status_code == 413
        assert "Stream exceeded size limit" in response.json()["detail"]
    
    def test_json_stream(self):
        """Test that JSON stream is buffered correctly."""
        json_data = b'{"key": "value", "number": 42}'
        response = client.post("/stream/ingest", content=json_data)
        assert response.status_code == 202
    
    def test_binary_stream(self):
        """Test that binary stream is buffered correctly."""
        binary_data = bytes([i % 256 for i in range(1000)])
        response = client.post("/stream/ingest", content=binary_data)
        assert response.status_code == 202
    
    def test_large_json_stream(self):
        """Test that large JSON stream under limit is accepted."""
        large_json = b'{"data": "' + (b"x" * 100000) + b'"}'
        response = client.post("/stream/ingest", content=large_json)
        assert response.status_code == 202
    
    def test_stream_boundary_minus_one(self):
        """Test stream 1 byte under the limit."""
        boundary_data = b"x" * (1048576 - 1)
        response = client.post("/stream/ingest", content=boundary_data)
        assert response.status_code == 202
    
    def test_stream_boundary_plus_one(self):
        """Test stream 1 byte over the limit."""
        boundary_data = b"x" * (1048576 + 1)
        response = client.post("/stream/ingest", content=boundary_data)
        assert response.status_code == 413
    
    def test_multiple_chunks_under_limit(self):
        """Test that multiple small chunks aggregate correctly."""
        # TestClient will send this as multiple chunks if we use multiple writes
        chunks = [b"x" * 10000 for _ in range(100)]  # 100 chunks of 10KB = 1MB
        data = b"".join(chunks)
        response = client.post("/stream/ingest", content=data)
        assert response.status_code == 202
    
    def test_chunked_stream_exceeds_limit(self):
        """Test that multiple chunks aggregating over limit returns 413."""
        chunks = [b"x" * 10000 for _ in range(105)]  # 105 chunks of 10KB = 1.05MB
        data = b"".join(chunks)
        response = client.post("/stream/ingest", content=data)
        assert response.status_code == 413
