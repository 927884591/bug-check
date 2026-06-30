# async-job-queue

## Applies When
- Changed files include jobs, queues, workers, schedulers, cron, webhooks, retries, background tasks, exports/imports, uploads/downloads, or long-running processing.
- Bug text mentions worker, job, queue, retry, timeout, cancel, duplicate, idempotent, dead letter, scheduler, cron, webhook, out of order, deploy restart, or stale callback.

## Inspect
- Enqueue path, payload schema, idempotency key, deduplication, retry policy, timeout, cancellation, and dead-letter behavior.
- Worker database writes, transaction boundaries, partial failure, and cleanup.
- Scheduler behavior across missed runs, duplicate runs, clock skew, daylight-saving changes, and deploy restarts.
- Webhook signature verification, replay handling, and ordering guarantees.
- User-visible progress, success, failure, retry, and cancel states.

## Handled When
- Repeated enqueue, retry, replay, and duplicate delivery are idempotent or explicitly rejected.
- Failed jobs preserve enough error evidence and reach retry/dead-letter paths correctly.
- Worker writes cannot partially corrupt state after timeout, cancellation, or crash.
- Deploy restarts and scheduler drift do not skip or duplicate critical work.
- UI/API status distinguishes pending, running, success, business failure, technical failure, cancelled, and retrying when relevant.

## Missing Means
- The fix assumes a background job runs exactly once.
- Retry or duplicate delivery can produce duplicate writes or notifications.
- Timeout, cancellation, dead-letter, or deploy restart behavior is untested.
- Job status is updated only on success and remains stale on failure.
- Webhook replay or out-of-order delivery is not considered where applicable.

## Verify
- Duplicate enqueue, retry, timeout, cancellation, and dead-letter behavior.
- Worker crash or injected failure after the first write.
- Out-of-order webhook or job completion when relevant.
- Scheduler missed run and deploy restart path where feasible.
- UI/API status after pending, success, failure, retry, and cancel states.

## Test Ideas
- Worker unit/integration test with duplicate payload and idempotency key.
- Failure-injection test proving rollback or cleanup.
- Scheduler test for missed and duplicate run decisions.
- Webhook replay test for duplicate and out-of-order events.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
