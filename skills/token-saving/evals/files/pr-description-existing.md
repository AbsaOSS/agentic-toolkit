## Summary

Implements the user registration and authentication endpoints for the platform API.

Adds:
- `POST /auth/register` — creates a new user account with email + password
- `POST /auth/login` — returns a JWT access token on successful credentials
- `POST /auth/logout` — invalidates the current session token in Redis
- Input validation via Pydantic v2 schemas (email format, password complexity)
- Password hashing with bcrypt

Migrations included. All endpoints covered by integration tests (pytest + TestClient).

---

## Update 2026-05-12 · commit 9f3a21b

- Added `POST /auth/password-reset/request` and `POST /auth/password-reset/confirm`
- Reset tokens expire after 1 hour; stored hashed in DB
- 8 new unit tests added for reset flow edge cases (expired, reuse, invalid token)
