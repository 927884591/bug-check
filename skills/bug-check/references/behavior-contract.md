# Behavior Contract

Use this contract before editing behavior-changing code. It separates known requirements from product decisions an AI must not invent.

For each material behavior, record:

```text
ID: C1
Source: specified | existing-contract | inferred | product-decision-required
Source evidence: exact user wording, file/test/API/schema path, documented rule, observed current behavior, or explicit assumption reason
Observable acceptance: what a user or system can observe
Impact surface: callers, consumers, state, permissions, persistence, lifecycle, tests
Open decision: none, or the exact product question
```

Source rules:

- `specified`: explicitly required by the user or accepted requirement; retain the exact wording or requirement reference.
- `existing-contract`: required by an existing test, type, API/schema, documented rule, or intentional current behavior; retain its path or identifier.
- `inferred`: a narrow implementation assumption that does not create new product semantics; record why it is reversible and compatible.
- `product-decision-required`: naming, units, automation, visibility, workflow, policy, or UX behavior with no authoritative source.

Do not convert `product-decision-required` into a passing acceptance claim. Ask when it blocks correct implementation; otherwise preserve the narrow existing behavior, keep the idea out of scope, and report it.

Keep the same `C1` ID through the diff, counterexample, and evidence stages. Before coding, turn each accepted behavior into an observable claim. Consider only relevant failure surfaces, including bad or empty input, loading/error state, permissions, retries, stale async work, concurrency, reload, cancellation, idempotency, and lifecycle cleanup.
