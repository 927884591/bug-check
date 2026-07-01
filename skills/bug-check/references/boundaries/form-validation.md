# form-validation

## Applies When
- Changed files include forms, dialogs, drawers, validators, schemas, field components, or submit handlers.
- Bug text mentions validation, required fields, duplicate save, disabled fields, hidden fields, max length, special characters, backend error, or stuck submit state.

## Do Not Select When
- The changed UI is read-only and has no editable fields, submit action, validation schema, or mutation payload.
- The form-like component is only a search/filter panel whose failure mechanism is pagination or list state; use ui-list-table instead.
- The backend contract changed but no client field behavior, validation, disabled state, or submit lifecycle changed; use api-contract instead.

## Inspect
- Field schema, visibility rules, default values, normalization, and dependent fields.
- Submit button disabled/loading/error behavior.
- Client validation and server validation mapping.
- Hidden/read-only/disabled field serialization.
- Duplicate-click, slow-request, failure, retry, and cancel paths.
- Mutation refresh and close-on-success behavior.

## Handled When
- Empty, max length, special characters, duplicate names, invalid dates, and end-before-start are handled where relevant.
- Hidden fields are not incorrectly required or submitted.
- Disabled/read-only fields cannot be edited through stale state.
- Backend validation errors stay visible and do not close the dialog as success.
- Repeated submit clicks cannot create duplicates or leave buttons stuck.
- Successful save updates the visible state, list/detail/cache, and form dirty state consistently.

## Missing Means
- Current code relies only on happy-path submit and has no branch for failed validation or slow requests.
- Hidden fields remain in the payload without an explicit reason.
- The UI shows success before the backend confirms business success.
- No test or manual verification covers a relevant validation branch.

## Verify
- Empty value, max length, duplicate, special characters, invalid date, and boundary date cases.
- Hidden field toggle before submit.
- Disabled/read-only state after async data loads.
- Slow request, failed request, retry, and repeated click.
- Backend validation response with field and global errors.
- Save success refreshes the affected list/detail/cache.

## Test Ideas
- Unit test for schema/normalization decisions.
- Integration test for server validation errors staying visible.
- E2E test for double-click submit creating one record.
- Regression test for hidden field not being submitted.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
