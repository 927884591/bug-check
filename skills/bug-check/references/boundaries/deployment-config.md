# deployment-config

## Applies When
- Changed files include env files, configuration, feature flags, deployment scripts, Docker, compose, Kubernetes, Helm, CI, startup, health checks, migrations, or compatibility code.
- Bug text mentions deploy, staging, production, env var, config, secret, feature flag, rollout, startup, health check, rollback, version skew, or compatibility.

## Inspect
- Local, test, staging, production, and CI config differences.
- Required env vars, defaults, secrets, base URLs, regions, time zones, and feature flags.
- Startup, shutdown, health checks, readiness, graceful drain, migration ordering, and worker/API version skew.
- Old/new frontend assets, mobile clients, workers, and APIs during rolling deploys.
- Optional integration fallback behavior.

## Handled When
- Required config has explicit defaults or fails fast with actionable errors.
- Feature flags handle disabled, enabled, partial rollout, and targeted user/tenant states.
- Startup/readiness does not report healthy before dependencies, migrations, or critical workers are ready.
- Old and new versions can coexist or have a deliberate rollout/migration plan.
- Secrets are not logged or committed, and missing optional integrations degrade safely.

## Missing Means
- The fix works only with local config assumptions.
- Missing env vars produce late, unclear runtime failures.
- Feature flag off/partial states are untested.
- Rolling deploy or worker/API version skew can break the contract.
- Config changes are treated as documentation rather than executable code paths.

## Verify
- Expected value, default value, and missing value for changed config.
- Local/test/staging/prod-equivalent env comparison where available.
- Feature flag disabled, enabled, and partially rolled out states.
- Startup/readiness failure when dependencies or migrations are unavailable.
- Old/new version compatibility for APIs, workers, and cached frontend assets when relevant.

## Test Ideas
- Unit test for config parsing and defaults.
- Startup smoke test with missing required env var.
- Feature-flag matrix test for off/on/targeted states.
- Compatibility test for old client/new API or new client/old API shape.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
