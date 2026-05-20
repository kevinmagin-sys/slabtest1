import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from stream_timeout import app

client = TestClient(app)

class TestStreamTimeoutBoundary:
    """Test the /stream/timeout_ingest endpoint."""
    
    def test_normal_stream_succeeds(self):
        """Test that normal stream completes successfully."""
        data = b"x" * 10000
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 202
        assert response.json()["detail"] == "Stream fully buffered and routed"
    
    def test_small_stream_within_timeout(self):
        """Test that small stream well within timeout succeeds."""
        data = b"x" * 1000
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 202
    
    def test_stream_at_size_limit(self):
        """Test that stream at 1MB limit is accepted."""
        data = b"x" * 1048576
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 202
    
    def test_stream_exceeds_size_limit(self):
        """Test that stream exceeding 1MB returns 413."""
        data = b"x" * (1048576 + 1)
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 413
        assert "Stream exceeded size limit" in response.json()["detail"]
    
    def test_json_stream_within_timeout(self):
        """Test that JSON stream completes within timeout."""
        json_data = b'{"key": "value", "data": [1, 2, 3, 4, 5]}'
        response = client.post("/stream/timeout_ingest", content=json_data)
        assert response.status_code == 202
    
    def test_binary_stream_within_timeout(self):
        """Test that binary stream completes within timeout."""
        binary_data = bytes([i % 256 for i in range(10000)])
        response = client.post("/stream/timeout_ingest", content=binary_data)
        assert response.status_code == 202
    
    def test_large_stream_within_limit(self):
        """Test that large stream within size and time limits succeeds."""
        large_data = b"x" * (1048576 - 1000)
        response = client.post("/stream/timeout_ingest", content=large_data)
        assert response.status_code == 202
    
    def test_empty_stream(self):
        """Test that empty stream is handled correctly."""
        response = client.post("/stream/timeout_ingest", content=b"")
        assert response.status_code == 202
    
    def test_boundary_size_minus_one(self):
        """Test stream 1 byte under the limit."""
        data = b"x" * (1048576 - 1)
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 202
    
    def test_boundary_size_plus_one(self):
        """Test stream 1 byte over the limit."""
        data = b"x" * (1048576 + 1)
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 413
    
    def test_multiple_chunks_aggregate_correctly(self):
        """Test that multiple chunks are aggregated for size checking."""
        # 50 chunks of 20KB = 1MB exactly
        chunks = [b"x" * 20000 for _ in range(50)]
        data = b"".join(chunks)
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 202
    
    def test_chunked_stream_over_limit(self):
        """Test that multiple chunks aggregating over limit returns 413."""
        # 55 chunks of 20KB = 1.1MB
        chunks = [b"x" * 20000 for _ in range(55)]
        data = b"".join(chunks)
        response = client.post("/stream/timeout_ingest", content=data)
        assert response.status_code == 413
