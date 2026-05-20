import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from forge import app, SlabSchema

client = TestClient(app)

class TestForgeEngine:
    """Test the /forge/engine endpoint."""
    
    def test_valid_payload_with_data_field(self):
        """Test that valid payload with 'data' field is processed."""
        payload = {"data": "test value"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
        assert response.json()["detail"] == "Accepted"
    
    def test_valid_nested_data_field(self):
        """Test that nested object in 'data' field is processed."""
        payload = {"data": {"key": "value", "nested": {"count": 42}}}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_valid_array_data_field(self):
        """Test that array in 'data' field is processed."""
        payload = {"data": [1, 2, 3, 4, 5]}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_valid_null_data_field(self):
        """Test that null value in 'data' field is processed."""
        payload = {"data": None}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_valid_string_data(self):
        """Test that string data is processed."""
        payload = {"data": "test string"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_valid_number_data(self):
        """Test that number data is processed."""
        payload = {"data": 42}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_valid_boolean_data(self):
        """Test that boolean data is processed."""
        payload = {"data": True}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_missing_data_field_returns_422(self):
        """Test that missing 'data' field returns 422."""
        payload = {"other_field": "value"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"] == "invalid_data"
    
    def test_empty_dict_payload_returns_422(self):
        """Test that empty dict returns 422."""
        payload = {}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 422
        assert response.json()["detail"] == "invalid_data"
    
    def test_extra_fields_accepted(self):
        """Test that extra fields are accepted (Pydantic allows by default)."""
        payload = {"data": "value", "extra_field": "extra"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_complex_nested_structure(self):
        """Test that complex nested structures are processed."""
        payload = {
            "data": {
                "level1": {
                    "level2": {
                        "array": [1, {"key": "value"}, [True, False, None]],
                        "string": "test"
                    }
                }
            }
        }
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    @patch('forge.queue_push')
    def test_queue_push_called(self, mock_queue):
        """Test that queue_push is called with processed payload."""
        payload = {"data": "test"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
        mock_queue.assert_called_once()
        # Verify the call arguments
        call_args = mock_queue.call_args
        assert call_args[0][1] == "DownstreamTopic"
    
    @patch('forge.transform')
    def test_transform_called(self, mock_transform):
        """Test that transform is called with validated data."""
        mock_transform.return_value = {"processed": {"data": "test"}}
        payload = {"data": "test"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
        mock_transform.assert_called_once()
        # Verify the call arguments
        call_args = mock_transform.call_args
        assert call_args[0][1] == "EngineLogic"
    
    def test_large_complex_payload(self):
        """Test that large complex payload is processed."""
        payload = {
            "data": {
                "large_array": [i for i in range(1000)],
                "large_string": "x" * 10000
            }
        }
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_deeply_nested_structure(self):
        """Test that deeply nested structure is processed."""
        # Create a deeply nested structure
        nested = {"value": 1}
        for _ in range(20):
            nested = {"nested": nested}
        payload = {"data": nested}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_unicode_data(self):
        """Test that unicode data is processed correctly."""
        payload = {"data": "Hello 世界 🚀 Мир"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
    
    def test_special_characters_in_data(self):
        """Test that special characters in data are processed."""
        payload = {"data": "Test\nwith\ttabs\rand\bspecial\\chars"}
        response = client.post("/forge/engine", json=payload)
        assert response.status_code == 202
