# 💉 Dependency Injection in Complyo

> Complyo verwendet FastAPI's `Depends()` für saubere Dependency Injection.

---

## 📋 Verfügbare Dependencies

### Datenbank & Cache

| Dependency | Beschreibung | Rückgabewert |
|------------|--------------|--------------|
| `get_db()` | PostgreSQL Connection Pool | `asyncpg.Pool` |
| `get_redis()` | Redis Client (optional) | `Optional[aioredis.Redis]` |

### Authentifizierung

| Dependency | Beschreibung | Rückgabewert |
|------------|--------------|--------------|
| `get_current_user()` | Authentifizierter User (required) | `dict` |
| `get_current_user_optional()` | Authentifizierter User (optional) | `Optional[dict]` |
| `require_admin()` | Admin-User (required) | `dict` |

### Services

| Dependency | Beschreibung | Rückgabewert |
|------------|--------------|--------------|
| `get_auth_service()` | Auth Service | `AuthService` |
| `get_stripe_service()` | Stripe Payment Service | `StripeService` |
| `get_news_service()` | Legal News Service | `NewsService` |
| `get_settings()` | App Konfiguration | `Settings` |

### Utilities

| Dependency | Beschreibung | Rückgabewert |
|------------|--------------|--------------|
| `get_client_ip()` | Client IP-Adresse | `str` |

---

## 🚀 Verwendung

### Import

```python
from dependencies import (
    get_db,
    get_redis,
    get_current_user,
    get_current_user_optional,
    require_admin,
    get_auth_service,
    get_settings,
    get_client_ip
)
```

### Beispiele

#### Einfache Datenbankabfrage

```python
from fastapi import APIRouter, Depends
from dependencies import get_db
import asyncpg

router = APIRouter()

@router.get("/users")
async def get_users(db: asyncpg.Pool = Depends(get_db)):
    async with db.acquire() as conn:
        users = await conn.fetch("SELECT id, email FROM users LIMIT 10")
    return {"users": [dict(u) for u in users]}
```

#### Authentifizierter Endpoint

```python
@router.get("/profile")
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Pool = Depends(get_db)
):
    async with db.acquire() as conn:
        profile = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            current_user["user_id"]
        )
    return {"profile": dict(profile)}
```

#### Admin-Only Endpoint

```python
@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    admin: dict = Depends(require_admin),
    db: asyncpg.Pool = Depends(get_db)
):
    async with db.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
    return {"message": "User deleted"}
```

#### Optionale Authentifizierung

```python
@router.get("/articles")
async def get_articles(
    user: Optional[dict] = Depends(get_current_user_optional),
    db: asyncpg.Pool = Depends(get_db)
):
    # Zeige personalisierte Artikel wenn eingeloggt
    if user:
        query = "SELECT * FROM articles WHERE user_id = $1"
        params = [user["user_id"]]
    else:
        query = "SELECT * FROM articles WHERE is_public = TRUE"
        params = []
    
    async with db.acquire() as conn:
        articles = await conn.fetch(query, *params)
    
    return {"articles": [dict(a) for a in articles]}
```

#### Mit Redis Cache

```python
from typing import Optional
import redis.asyncio as aioredis

@router.get("/stats")
async def get_stats(
    redis: Optional[aioredis.Redis] = Depends(get_redis),
    db: asyncpg.Pool = Depends(get_db)
):
    # Versuche Cache zuerst
    if redis:
        cached = await redis.get("stats:overview")
        if cached:
            return {"stats": json.loads(cached), "cached": True}
    
    # Berechne wenn nicht gecached
    async with db.acquire() as conn:
        stats = await conn.fetchrow("""
            SELECT 
                COUNT(*) as total_users,
                COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_users
            FROM users
        """)
    
    result = dict(stats)
    
    # Cache für 5 Minuten
    if redis:
        await redis.setex("stats:overview", 300, json.dumps(result))
    
    return {"stats": result, "cached": False}
```

#### Service Injection

```python
from dependencies import get_auth_service
from auth_service import AuthService

@router.post("/login")
async def login(
    email: str,
    password: str,
    auth: AuthService = Depends(get_auth_service)
):
    user = await auth.authenticate(email, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    token = auth.create_access_token(user["id"])
    return {"token": token, "user": user}
```

---

## 🔧 Integration in main_production.py

```python
from dependencies import startup, shutdown, get_db, get_current_user

app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await startup()  # Initialisiert DB Pool und Redis

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown()  # Cleanup
```

---

## 🆕 Migration von Global Variables

### Vorher (Globale Variablen)

```python
# In main_production.py
db_pool = None
auth_service = None

@app.on_event("startup")
async def startup():
    global db_pool, auth_service
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    auth_service = AuthService(db_pool)

# In routes
@app.get("/users")
async def get_users():
    async with db_pool.acquire() as conn:  # Globale Variable!
        ...
```

### Nachher (Dependency Injection)

```python
from dependencies import get_db, get_auth_service

@router.get("/users")
async def get_users(
    db: asyncpg.Pool = Depends(get_db),  # Injiziert!
    auth: AuthService = Depends(get_auth_service)  # Injiziert!
):
    async with db.acquire() as conn:
        ...
```

---

## ✅ Vorteile

1. **Testbarkeit:** Dependencies können in Tests einfach gemockt werden
2. **Explizite Abhängigkeiten:** Jeder Endpoint zeigt seine Abhängigkeiten
3. **Automatische Dokumentation:** OpenAPI zeigt Security-Requirements
4. **Kein Global State:** Keine versteckten Abhängigkeiten
5. **Type Hints:** Bessere IDE-Unterstützung

---

## 🧪 Testing mit Mocks

```python
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

def test_get_users():
    # Mock die Dependency
    mock_db = AsyncMock()
    mock_db.acquire.return_value.__aenter__.return_value.fetch.return_value = [
        {"id": "1", "email": "test@example.com"}
    ]
    
    # Override in der App
    app.dependency_overrides[get_db] = lambda: mock_db
    
    client = TestClient(app)
    response = client.get("/users")
    
    assert response.status_code == 200
    assert len(response.json()["users"]) == 1
    
    # Cleanup
    app.dependency_overrides.clear()
```


