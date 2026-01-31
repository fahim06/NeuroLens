# NeuroLens API Design Guidelines

## Principles

1. **REST conventions**: Use HTTP methods semantically
2. **Consistent responses**: Standard envelope for all responses
3. **Meaningful errors**: Structured error responses with codes
4. **Pagination**: All list endpoints support pagination
5. **Versioning**: All endpoints under `/api/v{version}`

## URL Structure

```
/api/v1/{resource}           # Collection
/api/v1/{resource}/{id}      # Single resource
/api/v1/{resource}/{id}/{sub-resource}  # Nested resource
```

## HTTP Methods

| Method | Use Case                          |
|--------|-----------------------------------|
| GET    | Retrieve resource(s)              |
| POST   | Create resource or trigger action |
| PUT    | Full resource update              |
| PATCH  | Partial resource update           |
| DELETE | Remove resource                   |

## Response Format

### Success Response

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "3.0.0"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": [ ... ]
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "uuid"
  }
}
```

## Status Codes

| Code | Meaning                |
|------|------------------------|
| 200  | Success                |
| 201  | Created                |
| 202  | Accepted (async)       |
| 400  | Bad Request            |
| 401  | Unauthorized           |
| 403  | Forbidden              |
| 404  | Not Found              |
| 415  | Unsupported Media Type |
| 422  | Validation Error       |
| 500  | Internal Error         |

## Pagination

All list endpoints accept:

- `skip`: Number of items to skip (default: 0)
- `limit`: Max items to return (default: 100, max: 1000)

Response includes:

```json
{
  "items": [ ... ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

## Authentication

- JWT Bearer tokens
- Header: `Authorization: Bearer <token>`
- Token refresh: `/api/v1/auth/refresh`

## Rate Limiting

Headers returned:

- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset timestamp
