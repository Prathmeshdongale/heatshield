# API Contract

## Overview
Define the purpose and scope of the HeatShield API here.

## Base URL

```text
http://localhost:3000/api
```

Replace this URL with the actual API base URL used by the project.

## Authentication
Document the authentication mechanism, required headers, and token format.

## Endpoints

### GET /health

- Purpose: Check API availability.
- Success response: Document the actual response schema.
- Error responses: Document applicable HTTP status codes.

### Add project-specific endpoints

For each endpoint, document:
- HTTP method and path
- Purpose
- Authentication requirements
- Path and query parameters
- Request body schema
- Success response and status code
- Error responses
- Example request and response

## Common HTTP Status Codes

- 200: Request successful.
- 201: Resource created.
- 400: Invalid request.
- 401: Authentication required.
- 403: Access forbidden.
- 404: Resource not found.
- 500: Internal server error.

## Versioning
Document the API versioning strategy here.

## Notes
These are documentation templates. Update them to match the implemented API.
