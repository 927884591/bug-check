# auth-permission

## Applies When
- Changed files include login, logout, session, middleware, guards, permission checks, roles, menus, protected routes, or auth headers.
- Bug text mentions 401, 403, unauthorized, forbidden, no permission, expired session, password expired, role, token, or direct route access.

## Do Not Select When
- The change only affects unauthenticated public content with no session, role, token, guard, or object-level access behavior.
- Permission words appear only in user-facing copy and no route, API, menu, button, or server-side authorization path changes.
- The failure is pure tenant scoping after authorization has already succeeded; use tenant-isolation instead.

## Inspect
- Login/logout/session-expired/password-expired/no-permission state machine.
- Route guards, API guards, object-level authorization, and middleware order.
- Menu visibility, button enabled state, route access, and API response behavior.
- Token refresh, auth headers, cookie/session storage, and logout cleanup.
- Error messages after refresh, direct URL access, and active user operations.

## Handled When
- Logged-out, logged-in, expired session, password expired, no-permission, and direct-route states are distinct.
- Active user actions are not mistaken for inactivity timeout.
- Menu, button, route, and API permission behavior agree.
- Server-side authorization is enforced for object-level data, not only UI visibility.
- Token/session cleanup removes sensitive and context-specific data.
- Error messages are accurate after refresh and direct navigation.

## Missing Means
- The fix hides a UI control without enforcing server-side access.
- 401 and 403 are collapsed into misleading behavior.
- Route guards and API guards disagree.
- Logout or session expiry leaves sensitive cached data behind.
- No evidence covers direct URL access or expired-session behavior.

## Verify
- Logged out, logged in, session expired, password expired, no permission, and direct route access.
- Menu, button, route, and API behavior for the same permission.
- Refresh on login page and protected page.
- Token refresh failure and logout cleanup.
- Object-level unauthorized access by ID or copied URL.

## Test Ideas
- Guard unit test for 401 versus 403 behavior.
- Integration test for direct URL access without permission.
- API authorization test for object-level access.
- Regression test for logout clearing cached permissions and sensitive data.

Handling statuses: `already handled`, `missing -> fixed`, `not applicable`.
