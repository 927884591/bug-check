# file-transfer-export

## Applies When
- Changed files include upload, download, import, export, file preview, CSV/XLSX/PDF generation, object storage, signed URLs, multipart transfer, attachments, or report generation.
- Bug text mentions upload, download, import, export, file size, file type, MIME, CSV, Excel, PDF, partial failure, cancel, retry, timeout, signed URL, content disposition, or corrupt file.

## Do Not Select When
- The changed code only displays already-loaded file metadata and does not upload, import, export, download, preview, or generate file bytes.
- Export/download words appear only in labels or navigation and no file response, storage, authorization, or row selection path changes.
- The core risk is generic object authorization with no file payload; use auth-permission or tenant-isolation instead.

## Inspect
- File size/type validation, MIME sniffing, extension checks, antivirus or scanning hooks, and unsafe file content handling.
- Streaming, buffering, multipart boundaries, cancellation, retry, timeout, resumability, and cleanup of partial files.
- Export query scope, tenant/user permission, row limits, pagination, ordering, filters, and snapshot consistency.
- Encoding, CSV injection, delimiters, newlines, Unicode, formulas, filenames, content disposition, and cache headers.
- User-visible progress, success, failure, partial success, duplicate submit, and retry states.

## Handled When
- Upload/import rejects invalid size, type, malformed content, unsafe names, and unauthorized destinations.
- Download/export includes only authorized scoped data and uses stable filters, ordering, and limits.
- Partial failure, cancellation, timeout, duplicate request, and retry cannot leave corrupt or duplicate files.
- Generated files preserve encoding, escaping, headers, filenames, and content type across browsers where relevant.
- Tests or runtime checks cover a representative large file, invalid file, and scoped export path.

## Missing Means
- The fix trusts client-provided file name, extension, MIME type, or row filters.
- Export reads all data without tenant/user scope, row limits, or a stable snapshot.
- Upload/import writes partial data before validation or without rollback/cleanup.
- Download responses omit content type, disposition, cache, or authorization behavior.
- Verification only checks a tiny happy-path file.

## Verify
- Empty, small, large, too-large, wrong-type, malformed, Unicode, duplicate, and formula-like file content.
- Cancel, retry, timeout, network failure, and partial upload/import/export failure.
- Cross-tenant or unauthorized download/export/import attempts.
- Browser download filename, content type, encoding, and cache behavior.
- Export row count, ordering, filters, pagination, and snapshot consistency.

## Test Ideas
- API test for invalid file type/size and unauthorized object access.
- Import test with malformed, duplicate, Unicode, and partial-failure rows.
- Export test for tenant scope, filters, ordering, escaping, and row limits.
- Runtime test for cancellation or timeout cleanup.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
