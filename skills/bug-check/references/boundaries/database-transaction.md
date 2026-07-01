# database-transaction

## Applies When
- Changed files include database access, repositories, models, migrations, SQL, ORM schemas, transactions, backfills, or data repair scripts.
- Bug text mentions transaction, migration, query, join, index, duplicate, unique constraint, rollback, partial write, soft delete, cascade, deadlock, or old data.

## Do Not Select When
- The change does not read, write, migrate, repair, or rely on persisted database state.
- Database words appear only in mocked tests, UI labels, or API types and no real query/transaction/schema path changes.
- The boundary is only request/response shape around existing persistence behavior; use api-contract instead.

## Inspect
- Actual query filters, joins, ordering, limits, indexes, and tenant/user scoping.
- Transaction boundaries, retries, rollback behavior, and cleanup after failure.
- Uniqueness, foreign keys, cascade, soft delete, restore, archival, and history behavior.
- Migration forward-safety, idempotency, production-data compatibility, and rollback plan.
- Data repair/backfill separation from application code.

## Handled When
- Queries include correct filters, ordering, limits, and context scope.
- Multi-step writes use a transaction or have documented compensating behavior.
- Failure and retry cannot leave partial or duplicate data.
- Migrations are safe for existing null, duplicate, malformed, old-version, and large-volume records.
- Data repair includes verification queries and does not hide application bugs.

## Missing Means
- The fix only changes API/UI behavior while the persisted data path remains inconsistent.
- Multi-step writes can partially commit without rollback or cleanup.
- Migration assumes clean production data without evidence.
- Tenant/user scope is missing from query or index design.
- No verification reads data back from the persistence layer.

## Verify
- Read-back after create/update/delete and failed mutation.
- Transaction rollback on mid-operation failure.
- Duplicate, null, missing, malformed, old-version, and large-volume records.
- Migration dry run or local test database run where feasible.
- Verification query for backfill or data repair.

## Test Ideas
- Repository test for query scope and ordering.
- Transaction test that injects failure and proves rollback.
- Migration fixture with old/null/duplicate records.
- Data-repair smoke test with before/after verification query.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
