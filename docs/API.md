# Zendesk Voice Server API Documentation

This document describes the REST API endpoints provided by the Zendesk Voice Server.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, the API does not require authentication. In production, consider implementing API key authentication or OAuth2.

## Endpoints

### 1. Health Check

**GET** `/health`

Check the server health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "zendesk-voice-server",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

**Status Codes:**
- `200 OK` - Server is healthy

---

### 2. Call Events Manager

**POST** `/call_events_manager`

Processes voice call events and automatically creates Zendesk tickets.

**Request Body:**
```json
{
  "call": {
    "call_id": "call_123456789",
    "from_number": "+15551234567",
    "call_status": "ended",
    "start_timestamp": 1640995200000,
    "end_timestamp": 1640995260000,
    "duration_ms": 60000,
    "transcript": "User: Hello, I need help with my account.\nAgent: Hi, I'll be happy to help you with your account.",
    "call_analysis": {
      "call_summary": "Customer called for account support",
      "custom_analysis_data": {
        "name_of_caller": "John Doe",
        "email_to_reach": "john.doe@example.com",
        "interested_in_AI": "Yes",
        "caller_need": "Account verification"
      }
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "ticket_id": 12345,
  "message": "Created Zendesk ticket 12345"
}
```

**Status Codes:**
- `200 OK` - Call processed successfully
- `400 Bad Request` - Invalid request data
- `500 Internal Server Error` - Server error

**Notes:**
- Only processes calls with `call_status: "ended"`
- Prevents duplicate processing of the same call
- Creates Zendesk tickets with appropriate tags and descriptions

---

### 3. Manual Ticket Creation

**POST** `/create_zendesk_ticket`

Manually create a Zendesk ticket for testing or administrative purposes.

**Request Body:**
```json
{
  "subject": "Manual Test Ticket",
  "description": "This is a manually created ticket for testing purposes.",
  "requester_phone": "+15551234567",
  "tags": ["manual", "test", "voice-call"],
  "public": false
}
```

**Response:**
```json
{
  "success": true,
  "ticket": {
    "id": 12346,
    "subject": "Manual Test Ticket",
    "status": "open",
    "requester_id": 67890,
    "tags": ["manual", "test", "voice-call"]
  }
}
```

**Status Codes:**
- `200 OK` - Ticket created successfully
- `400 Bad Request` - Missing required fields
- `500 Internal Server Error` - Zendesk API error

**Required Fields:**
- `subject` - Ticket subject line
- `description` - Ticket description/body
- `requester_phone` - Phone number of the requester

**Optional Fields:**
- `tags` - Array of tags (default: `["voice-call", "automated"]`)
- `public` - Whether the comment is public (default: `false`)

---

### 4. Zendesk Flow Test

**GET** `/test_zendesk_flow`

Test the Zendesk integration by creating and updating a test ticket.

**Response:**
```json
{
  "success": true,
  "test_results": {
    "user_search": 1,
    "ticket_created": true,
    "ticket_id": 12347,
    "ticket_updated": true
  },
  "message": "Zendesk integration test completed successfully"
}
```

**Status Codes:**
- `200 OK` - Test completed successfully
- `500 Internal Server Error` - Test failed

**Notes:**
- Creates a test ticket with phone number `+15551234567`
- Updates the ticket status to "solved"
- Useful for verifying Zendesk API connectivity

---

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common error scenarios:

### 400 Bad Request
- Missing required fields
- Invalid data format
- Invalid phone number format

### 500 Internal Server Error
- Zendesk API errors
- Firebase connection issues
- Server configuration problems

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Data Validation

### Phone Numbers
- Must be valid phone number format
- Supports international formats
- Automatically cleaned and normalized

### Call Data
- `call_id` must be unique
- `call_status` must be "ended" for processing
- Timestamps must be valid Unix timestamps (milliseconds)

### Ticket Data
- Subject length: 1-100 characters
- Description length: 1-10,000 characters
- Tags: Array of strings, max 50 characters each

## Integration Examples

### cURL Examples

**Health Check:**
```bash
curl -X GET http://localhost:5000/health
```

**Process Call Event:**
```bash
curl -X POST http://localhost:5000/call_events_manager \
  -H "Content-Type: application/json" \
  -d '{
    "call": {
      "call_id": "call_123",
      "from_number": "+15551234567",
      "call_status": "ended",
      "start_timestamp": 1640995200000,
      "end_timestamp": 1640995260000,
      "duration_ms": 60000,
      "transcript": "User: Hello\nAgent: Hi",
      "call_analysis": {
        "call_summary": "Test call"
      }
    }
  }'
```

**Create Manual Ticket:**
```bash
curl -X POST http://localhost:5000/create_zendesk_ticket \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Test Ticket",
    "description": "Test description",
    "requester_phone": "+15551234567",
    "tags": ["test"]
  }'
```

### Python Examples

```python
import requests
import json

# Health check
response = requests.get('http://localhost:5000/health')
print(response.json())

# Process call event
call_data = {
    "call": {
        "call_id": "call_123",
        "from_number": "+15551234567",
        "call_status": "ended",
        "start_timestamp": 1640995200000,
        "end_timestamp": 1640995260000,
        "duration_ms": 60000,
        "transcript": "User: Hello\nAgent: Hi",
        "call_analysis": {
            "call_summary": "Test call"
        }
    }
}

response = requests.post(
    'http://localhost:5000/call_events_manager',
    json=call_data
)
print(response.json())
```

## Monitoring and Logging

The server provides comprehensive logging for monitoring:

- Request/response logging
- Zendesk API interactions
- Error tracking
- Performance metrics

Logs include:
- Timestamp
- Log level
- Message
- Request details (when applicable)

## Security Considerations

For production deployment:

1. **Implement authentication** (API keys, OAuth2)
2. **Use HTTPS** for all communications
3. **Validate input data** thoroughly
4. **Implement rate limiting**
5. **Monitor for suspicious activity**
6. **Keep dependencies updated** 