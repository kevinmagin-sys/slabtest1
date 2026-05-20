# SlabTest1 - FastAPI Ingestion Boundary

A FastAPI application implementing a data ingestion boundary with schema validation, size enforcement, and error handling.

## Features

- **Schema Validation**: Enforces strict schema with UUID identifier, ISO8601 timestamp, and JSON payload data
- **Unknown Field Rejection**: Rejects requests with extra fields
- **Size Enforcement**: Prevents payloads exceeding 1MB
- **Error Handling**: Returns appropriate HTTP status codes (202, 422, 413)
- **Metrics Emission**: Hooks for external metrics collection
- **Queue Routing**: Integration point for downstream message processing

## Schema

```json
{
  "identifier": "<uuid>",
  "timestamp": "<ISO8601 datetime>",
  "payload_data": {
    "<key>": "<any JSON value>"
  }
}
```

## Installation

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
uvicorn app:app --reload
```

The server will start at `http://localhost:8000`

## Testing

Run the test suite:

```bash
pytest test_app.py -v
```

## API Endpoint

### POST /ingest

Accepts JSON payloads matching the SlabPayload schema.

**Success Response (HTTP 202):**
```json
{"detail": "Accepted for processing"}
```

**Schema Validation Error (HTTP 422):**
```json
{"detail": [{"type": "...", "loc": [...], "msg": "..."}]}
```

**Payload Too Large Error (HTTP 413):**
```json
{"detail": "Payload size exceeded limit"}
```

## Test Coverage

The test suite covers:

1. **Schema Validation Tests**
   - Valid payload creation
   - Missing required fields
   - Unknown fields rejection
   - Invalid UUID format
   - Invalid datetime format

2. **Endpoint Tests**
   - Valid ingestion requests
   - Invalid JSON
   - Missing required fields
   - Invalid field formats
   - Extra fields
   - Oversized payloads
   - Nested structures
   - Empty payload data

## Example Usage

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-05-20T19:23:37Z",
    "payload_data": {
      "message": "Hello, World!",
      "count": 42
    }
  }'
```
