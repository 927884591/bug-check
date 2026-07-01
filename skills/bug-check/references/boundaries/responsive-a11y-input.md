# responsive-a11y-input

## Applies When
- Changed files include responsive layouts, navigation, buttons, inputs, forms, tables, menus, mobile breakpoints, keyboard handlers, focus styles, labels, or pointer/touch interactions outside overlays.
- Bug text mentions mobile, viewport, responsive, overflow, keyboard, tab order, focus, screen reader, label, touch, hover, disabled, input, zoom, or hit target.

## Do Not Select When
- The change is data, API, config, or backend-only with no rendered interactive UI or layout behavior.
- The only focus/keyboard behavior is inside a modal, drawer, popover, or portal overlay; use ui-overlay-focus instead.
- The UI change is static copy with no responsive layout, semantic element, keyboard, touch, or input-state behavior.

## Inspect
- Layout at small, medium, large, zoomed, and constrained viewports, including overflow and sticky/fixed elements.
- Keyboard navigation, focus order, visible focus, activation keys, skip paths, and non-pointer operation.
- Accessible names, labels, descriptions, errors, required/disabled state, and semantic element choice.
- Touch target size, hover-only controls, pointer cancellation, scrolling, virtual keyboard, and safe-area behavior.
- Loading, error, empty, disabled, permission, and validation states in responsive views.

## Handled When
- Content and controls remain usable without overlap, clipping, hidden required actions, or horizontal scroll surprises.
- Keyboard users can discover, focus, activate, and leave every interactive control in logical order.
- Inputs and controls expose accurate labels, errors, disabled/required state, and semantics to assistive tech.
- Touch and pointer behavior does not rely on hover-only affordances or tiny hit targets.
- Tests or runtime checks cover at least one mobile/constrained viewport and keyboard-only path when relevant.

## Missing Means
- The fix only works at the developer's desktop viewport.
- A custom clickable element lacks semantic role, keyboard activation, label, or visible focus.
- Hover-only controls hide required actions on touch devices.
- Virtual keyboard, zoom, sticky headers, or long labels make controls unreachable or overlapping.
- Verification only uses mouse clicks and does not cover keyboard or mobile layout.

## Verify
- Narrow mobile viewport, tablet/medium viewport, desktop, zoomed text, and long content.
- Tab, Shift+Tab, Enter, Space, Escape where relevant, and visible focus after validation or rerender.
- Screen reader-accessible labels, descriptions, errors, required/disabled state, and semantic roles.
- Touch target size, hover replacement, virtual keyboard, scrolling, and safe-area behavior.
- Loading, error, empty, disabled, and permission-denied states at constrained widths.

## Test Ideas
- Component or E2E test for keyboard navigation and activation.
- Accessibility assertion for labels, roles, errors, and disabled/required state.
- Visual or Playwright check for mobile/zoomed viewport with long text.
- Regression test for touch-accessible actions that were previously hover-only.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
