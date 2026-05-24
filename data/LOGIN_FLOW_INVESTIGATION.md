# Login Flow Investigation: mail@panoart360.de
Date: 2026-05-22

## 1. Backend Logs (complyo-backend, tail -50)
No login-related errors in recent logs. Only repeated health check hits and:
```
Error getting variant assignment: relation "cookie_ab_tests" does not exist
```
No 401s or auth errors logged at time of investigation.

## 2. Running Containers
| Name              | Image          | Port              | Status   |
|-------------------|----------------|-------------------|----------|
| complyo-backend   | legal-backend  | 127.0.0.1:8002    | healthy  |
| complyo-dashboard | legal-dashboard| 127.0.0.1:3001    | unhealthy|
| complyo-postgres  | postgres:15-alpine | 127.0.0.1:5433 | healthy |
| complyo-redis     | redis:7-alpine | 127.0.0.1:6380    | healthy  |

Note: Container is named `complyo-backend` (not `complyo-backend-direct`).

## 3. Login Endpoint Response
```
curl -X POST http://localhost:8002/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"mail@panoart360.de","password":"test"}'
```
Response:
```json
{"detail":"Ungültige Zugangsdaten"}
```
HTTP 401 Unauthorized. The password "test" is incorrect.

## 4. DB User Record
Query: `SELECT id, email, role, onboarding_completed, is_active, created_at FROM users WHERE email='mail@panoart360.de';`

| id | email              | role     | onboarding_completed | is_active | created_at                    |
|----|--------------------|----------|----------------------|-----------|-------------------------------|
| 5  | mail@panoart360.de | customer | t                    | t         | 2026-03-23 09:01:05.134947+00 |

User EXISTS. Account is active (`is_active = true`), onboarding completed. No account lock issues at DB level.

## 5. Login Endpoint Logic (auth_routes.py:156-173)
```python
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest):
    try:
        user = await auth_service.authenticate(body.email, body.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Zugangsdaten"
            )
        ...
```
Rate-limited to 5 attempts/minute.

## 6. authenticate() Method (auth_service.py:107-161)
Flow:
1. Check Redis for brute-force lockout key `login_fail:<email>` — if >= MAX_ATTEMPTS, raises HTTP 429.
2. Query DB: `SELECT ... FROM users WHERE email = $1 AND is_active = TRUE`
3. If user not found → increment Redis fail counter → return None → 401
4. bcrypt.checkpw(password, password_hash) — if mismatch → increment Redis fail counter → return None → 401
5. On success → delete Redis fail counter → return user dict (without password_hash)

## Root Cause
The password "test" does not match the bcrypt hash stored for mail@panoart360.de.
The user record is valid (active, onboarding done, role=customer). The 401 `"Ungültige Zugangsdaten"` is the expected response for a wrong password.

**Possible causes:**
- User registered with a different password
- Password was changed
- Possible brute-force lockout if many prior failed attempts (check Redis key `login_fail:mail@panoart360.de`)

## Redis Lockout Check Command
```bash
docker exec complyo-redis redis-cli -p 6379 GET "login_fail:mail@panoart360.de"
```
