# Routing Rules

Use this file before loading boundary cards. The goal is to route changed files and the bug description to a small context pack, not to read the whole repository.

## Inputs

Use:
- changed file paths from git diff, staged files, explicit `--files`, or the user's report
- diff hunks when available
- bug description words, error messages, and status codes
- project structure signals such as package files, API folders, migration folders, worker folders, and test folders
- nearby tests in the same directory, `__tests__`, `tests`, or matching `*.test.*` and `*.spec.*`

## Output Tags

Each route returns:
- boundary tags
- boundary card files to load
- suggested source/test files to read next
- focused inspection targets
- areas to avoid until evidence makes them relevant

## Routes

### list-table-ui

Signals:
- paths: `**/*List*`, `**/*Table*`, `**/pages/**`, `**/components/**`, `**/views/**`
- words: search, filter, reset, pagination, page, selected row, select all, empty, delete, sort

Boundary tags:
- `ui-list-table`
- `state-cache-sync`

Load files:
- `references/boundaries/ui-list-table.md`
- `references/boundaries/state-cache-sync.md`

Inspect first:
- search, filter, sort, and page index state
- selected rows and all-select state
- list/detail/count refresh after mutation
- nearby component or integration tests

Do not read yet:
- unrelated routes
- global styles
- the full services directory

### form-validation

Signals:
- paths: `**/*Form*`, `**/*Dialog*`, `**/*Modal*`, `**/forms/**`, `**/validators/**`
- words: form, validation, submit, save, duplicate, required, disabled, hidden, max length, error message

Boundary tags:
- `form-validation`
- `api-contract`
- `state-cache-sync`

Load files:
- `references/boundaries/form-validation.md`
- `references/boundaries/api-contract.md`
- `references/boundaries/state-cache-sync.md`

Inspect first:
- form schema and field visibility rules
- submit disabled/loading/error paths
- backend validation error handling
- mutation refresh after save

Do not read yet:
- unrelated list rendering
- unrelated deployment config

### api-contract

Signals:
- paths: `**/api/**`, `**/client/**`, `**/clients/**`, `**/request/**`, `**/requests/**`, `**/service/**`, `**/services/**`, `**/controllers/**`, `**/routes/**`
- words: 400, 401, 403, 404, 409, 422, 500, response, request, params, headers, body, serialization, DTO, schema, OpenAPI

Boundary tags:
- `api-contract`

Load files:
- `references/boundaries/api-contract.md`

Inspect first:
- request method, URL, params, headers, and body shape
- response schema and error body handling
- generated client or shared DTO updates
- status-code branches in callers
- auth headers and `auth-permission` only when the bug mentions 401, 403, auth, session, token, role, or permission

Do not read yet:
- unrelated UI layout files
- full database migrations unless persistence is implicated

### auth-permission

Signals:
- paths: `**/auth/**`, `**/permission/**`, `**/permissions/**`, `**/session/**`, `**/login/**`, `**/middleware/**`, `**/guard/**`
- words: login, logout, session, token, permission, role, unauthorized, forbidden, 401, 403, password, expired

Boundary tags:
- `auth-permission`

Load files:
- `references/boundaries/auth-permission.md`

Inspect first:
- route/API guards and object-level authorization
- session-expired and no-permission branches
- menu/button/API permission consistency
- token and sensitive-data exposure
- `security-sensitive-data` only when the bug involves tokens, cookies, secrets, logs, downloads, exports, private URLs, or rendered unsafe content

Do not read yet:
- unrelated table pagination
- unrelated worker queues

### tenant-context

Signals:
- paths: `**/tenant/**`, `**/project/**`, `**/site/**`, `**/organization/**`, `**/org/**`, `**/workspace/**`
- words: tenant, project, site, org, organization, workspace, switch, isolation, leak, cross tenant

Boundary tags:
- `tenant-isolation`
- `state-cache-sync`
- `security-sensitive-data`

Load files:
- `references/boundaries/tenant-isolation.md`
- `references/boundaries/state-cache-sync.md`
- `references/boundaries/security-sensitive-data.md`

Inspect first:
- active tenant/project/site/org propagation
- cache keys, selected rows, dropdowns, and subscriptions after switch
- detail URLs, exports, websocket/polling requests
- authorization checks on server-side reads and writes

Do not read yet:
- unrelated visual styling
- unrelated deployment scripts

### database-persistence

Signals:
- paths: `**/db/**`, `**/database/**`, `**/models/**`, `**/repositories/**`, `**/repo/**`, `**/migrations/**`, `**/prisma/**`, `**/sql/**`
- words: transaction, migration, query, join, index, duplicate, soft delete, rollback, deadlock, constraint, backfill

Boundary tags:
- `database-transaction`
- `tenant-isolation`
- `api-contract`

Load files:
- `references/boundaries/database-transaction.md`
- `references/boundaries/tenant-isolation.md`
- `references/boundaries/api-contract.md`

Inspect first:
- query filters, joins, limits, ordering, and indexes
- transaction boundaries and rollback behavior
- migration safety against existing data
- tenant/user scoping

Do not read yet:
- unrelated component CSS
- unrelated browser-only code

### queue-worker

Signals:
- paths: `**/jobs/**`, `**/job/**`, `**/queue/**`, `**/queues/**`, `**/worker/**`, `**/workers/**`, `**/scheduler/**`, `**/cron/**`, `**/webhook/**`
- words: queue, worker, job, retry, dead letter, scheduler, cron, webhook, duplicate, idempotent, timeout, out of order

Boundary tags:
- `async-job-queue`

Load files:
- `references/boundaries/async-job-queue.md`

Inspect first:
- idempotency keys and deduplication
- retry, timeout, cancellation, and dead-letter behavior
- worker/database transaction boundaries
- deploy restart and clock-skew behavior
- `database-transaction` only when storage writes, migrations, partial writes, or rollback are in scope
- `deployment-config` only when config, rollout, startup, health check, or release compatibility is in scope outside normal worker restart handling

Do not read yet:
- unrelated UI components
- unrelated static assets

### deployment-config

Signals:
- paths: `**/.env*`, `**/config/**`, `**/deploy/**`, `**/deployment/**`, `**/docker/**`, `**/Dockerfile`, `**/compose*.yml`, `**/helm/**`, `**/k8s/**`, `**/ci/**`, `.github/**`
- words: env, config, deploy, staging, production, feature flag, compatibility, health check, startup, rollback, secret

Boundary tags:
- `deployment-config`
- `api-contract`
- `security-sensitive-data`

Load files:
- `references/boundaries/deployment-config.md`
- `references/boundaries/api-contract.md`
- `references/boundaries/security-sensitive-data.md`

Inspect first:
- environment variable defaults and required secrets
- feature flag states and rollout targeting
- startup/readiness/migration/deploy ordering
- old/new version compatibility

Do not read yet:
- unrelated form fields
- unrelated table rendering

### security-sensitive-data

Signals:
- paths: `**/security/**`, `**/download/**`, `**/export/**`, `**/upload/**`, `**/render/**`, `**/html/**`, `**/logger/**`, `**/logging/**`
- words: xss, injection, sanitize, token, cookie, secret, password, private, PII, sensitive, download, export, log, HTML

Boundary tags:
- `security-sensitive-data`
- `auth-permission`
- `tenant-isolation`

Load files:
- `references/boundaries/security-sensitive-data.md`
- `references/boundaries/auth-permission.md`
- `references/boundaries/tenant-isolation.md`

Inspect first:
- unsafe rendering and link/download permissions
- log, telemetry, screenshot, and export contents
- server-side authorization and object-level access
- token, cookie, and secret handling

Do not read yet:
- unrelated cosmetic layout
- unrelated pagination state unless the leak appears there
