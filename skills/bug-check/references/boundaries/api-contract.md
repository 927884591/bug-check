# api-contract

## Applies When
- Changed files include API clients, controllers, routes, services, DTOs, request wrappers, validation schemas, generated clients, or OpenAPI/spec files.
- Bug text mentions status codes, request params, response shape, serialization, missing fields, null values, enum values, auth headers, or third-party integration.

## Inspect
- Method, path, route params, query params, headers, body shape, content type, and auth context.
- Frontend/client types, API validation schemas, service DTOs, generated clients, and tests.
- 200/201/204/400/401/403/404/409/422/429/500 handling.
- Error body shape and user-facing/API-facing error mapping.
- Serialization of dates, decimals, booleans, IDs, large integers, Unicode, nested arrays, and cursors.
- Backward compatibility for existing clients.

## Handled When
- Request and response schemas match across callers, handlers, validators, generated clients, and tests.
- Every status code relevant to the change has explicit behavior.
- Missing field, null, empty array/object, omitted optional value, and unknown enum behavior is defined.
- Auth context and permission failures are represented consistently.
- Serialization edge cases preserve data shape and precision.
- Contract changes preserve or deliberately migrate older clients.

## Missing Means
- The fix changes only one side of the API boundary.
- Error handling assumes all failures have the same status/body shape.
- Optional/null/missing/empty values are treated interchangeably without evidence.
- No test or runtime check covers the actual request/response shape.

## Verify
- Inspect real request and response before and after the fix when possible.
- Test success, validation failure, auth failure, not found, conflict, rate limit, and server error as relevant.
- Verify omitted, null, empty, unknown enum, large number, Unicode, nested array, and pagination cursor cases when in scope.
- Confirm generated clients/specs/types stay in sync.
- Confirm old clients or cached frontend assets still behave acceptably when compatibility matters.

## Test Ideas
- Contract test for request and response schema.
- Handler test for relevant status-code branches.
- Client test for error body parsing and user-facing message mapping.
- Serialization regression test for date, decimal, ID, Unicode, and cursor values.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
