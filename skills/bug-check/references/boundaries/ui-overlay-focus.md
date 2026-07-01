# ui-overlay-focus

## Applies When
- Changed files include modals, dialogs, drawers, popovers, menus, tooltips, portals, overlays, focus management, keyboard handlers, or scroll locking.
- Bug text mentions focus lost, focus trap, screen reader, keyboard, Escape, Enter, close, cancel, backdrop, z-index, portal, body scroll, inert background, or overlay stuck.

## Do Not Select When
- The changed UI is inline page content with no modal, drawer, popover, menu, tooltip, portal, overlay, scroll lock, or outside-click behavior.
- The issue is ordinary keyboard access or responsive layout outside an overlay; use responsive-a11y-input instead.
- Overlay words appear only in styles or copy and no open/close, focus, portal, or cleanup lifecycle changes.

## Inspect
- Open, close, cancel, confirm, backdrop click, Escape, route change, and unmount paths.
- Initial focus, focus trap, focus restoration, tab order, ARIA name/role/state, and keyboard-only behavior.
- Body/page scroll lock, inert background, pointer events, nested overlays, and cleanup after interrupted close animation.
- Portal container, stacking context, z-index, outside click boundaries, and mobile viewport behavior.
- Loading, error, disabled, and permission states inside the overlay.

## Handled When
- Opening moves focus to a meaningful element and closing restores focus to the invoking control when possible.
- Keyboard users can operate and escape the overlay without reaching inert background content.
- Screen reader role, label, description, modal state, and disabled/error states are represented accurately.
- Scroll lock, event listeners, timers, animation state, and portal nodes are cleaned up on every close/unmount path.
- Nested overlays, interrupted animations, and route changes do not leave stuck focus, scroll lock, or hidden UI.

## Missing Means
- The fix only changes visible styling while focus, keyboard, or screen reader behavior remains undefined.
- Close/cancel paths do not share cleanup with confirm or route/unmount cleanup.
- Scroll lock or global listeners are added without guaranteed removal.
- Tests or manual checks only click with a mouse and do not cover keyboard or interrupted close behavior.

## Verify
- Open by mouse and keyboard, then close by button, Escape, backdrop, cancel, confirm, and route change.
- Tab and Shift+Tab stay in the overlay; focus returns after close.
- Screen reader name/role/state are present for the overlay and critical controls.
- Body scroll, background click, event listeners, and portal nodes are cleaned up after close and unmount.
- Nested overlay or interrupted animation path when relevant.

## Test Ideas
- Component/integration test for focus restoration after close.
- Keyboard test for Tab trap, Escape close, and disabled confirm behavior.
- Cleanup test for body scroll lock and global listener removal after unmount.
- Accessibility assertion for dialog role/name and `aria-modal` or equivalent framework behavior.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
