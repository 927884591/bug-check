# i18n-timezone-format

## Applies When
- Changed files include date/time formatting, schedules, calendars, reports, money, decimals, numeric input, locale dictionaries, currency, timezone conversion, or export formatting.
- Bug text mentions timezone, DST, locale, language, date boundary, midnight, month end, week start, currency, decimal, rounding, percent, large number, or inconsistent format.

## Do Not Select When
- The change does not parse, compute, compare, store, translate, sort, or format dates, times, numbers, currency, or locale text.
- Date or locale words appear only in static copy and no boundary date, numeric precision, or fallback behavior changes.
- The issue is only API serialization shape with no locale/timezone/formatting rule; use api-contract instead.

## Inspect
- Source-of-truth timezone, storage format, API serialization, display locale, parsing, and round-trip conversion.
- Date boundaries across midnight, DST start/end, month/year end, leap day, and user/server timezone differences.
- Currency, decimal precision, rounding mode, percent, thousands separators, negative values, and large IDs or numbers.
- Locale fallback, missing translations, pluralization, sort/collation behavior, and right-to-left or long text where relevant.
- Tests, snapshots, exports, and reports that encode dates, numbers, or translated labels.

## Handled When
- Stored values, API values, and displayed values use explicit timezone and locale rules.
- Date ranges include the intended endpoints across DST, midnight, week/month/year boundaries, and server/client timezone differences.
- Currency and decimal calculations preserve precision and use deliberate rounding and formatting.
- Missing locale strings degrade predictably and do not break layout, parsing, or validation.
- Tests or runtime checks cover at least one boundary date and one representative locale/number format when relevant.

## Missing Means
- Code parses or formats dates with implicit local timezone assumptions.
- Date filters use string slicing or inclusive/exclusive boundaries without proving timezone behavior.
- Money, decimals, percentages, or large numbers are rounded, parsed, or serialized through unsafe floating-point or string paths.
- UI, export, and API formats diverge without a documented contract.
- Verification only covers the developer's current locale and current date.

## Verify
- User timezone differs from server timezone.
- DST transition day, midnight, month end, year end, leap day, and inclusive/exclusive range endpoints.
- Currency minor units, rounding, negative values, zero, large values, decimal separators, and percent formatting.
- Locale fallback, long translated labels, plural forms, and export/report output.
- API, UI, and downloaded/exported values match the intended contract.

## Test Ideas
- Unit test for date range construction across DST and timezone changes.
- Serialization test for API date/time round trips.
- Formatting test for currency, decimal, percent, negative, and large values.
- Locale fallback test for missing translation and long translated text.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
