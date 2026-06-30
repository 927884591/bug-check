# security-sensitive-data

## Applies When
- Changed files include security, auth, logging, telemetry, downloads, exports, uploads, rendering, rich text, HTML, templates, URLs, cookies, tokens, or secrets.
- Bug text mentions XSS, injection, sanitize, unsafe HTML, token, cookie, secret, password, private URL, PII, sensitive data, download, export, copied link, logs, or screenshots.

## Inspect
- User-controlled HTML/text in URL params, backend messages, table cells, tooltips, dialogs, rich text, and exported files.
- Download, preview, share, and detail links for permission bypass.
- Logs, analytics, telemetry, screenshots, error reports, and traces for secrets or personal data.
- Server-side authorization, object-level access control, rate limits, and secret handling.
- CSV/Excel formulas, filenames, paths, and content-disposition behavior.

## Handled When
- User-controlled content is escaped, sanitized, or rendered through a deliberate safe path.
- Download/share/detail URLs require server-side authorization and cannot bypass permissions through copied links or stale tokens.
- Passwords, tokens, cookies, secrets, tenant IDs, private URLs, and personal data are absent from logs and screenshots unless explicitly safe.
- CSV/Excel exports neutralize formula injection when user-controlled content is included.
- Rate limits, object-level authorization, and secret storage are enforced server-side.

## Missing Means
- The fix relies only on frontend hiding or client-side checks for sensitive data.
- Backend messages or rich text are rendered as HTML without sanitization evidence.
- Logs or telemetry include raw secrets, tokens, cookies, private URLs, or personal data.
- Exports/downloads are verified only through UI visibility, not server authorization.
- No negative test covers unauthorized access or unsafe content.

## Verify
- Rendered user-controlled text with `<script>`, HTML entities, URLs, Unicode, and long text.
- Copied download/detail/share link with a different user or without permission.
- Logs, telemetry, screenshots, and error reports from the failing path.
- CSV/Excel export with formula-like values.
- API unauthorized access by object ID and rate-limit behavior where relevant.

## Test Ideas
- Rendering test proving escaping or sanitization.
- API authorization test for copied link or object ID.
- Log snapshot/unit test redacting sensitive fields.
- Export test neutralizing formula injection.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
