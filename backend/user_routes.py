"""
User Routes - User Profile & Domain Locks
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
import bcrypt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/user", tags=["user"])
security = HTTPBearer()

# Global references (set in main_production.py)
db_pool = None
auth_service = None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from Authorization header"""
    from auth_routes import get_current_user as auth_get_user
    return await auth_get_user(credentials)

@router.get("/domain-locks")
async def get_domain_locks(current_user: dict = Depends(get_current_user)):
    """
    Holt alle Domain-Locks eines Users
    
    Returns:
        List of Domain-Locks mit Status (locked/unlocked)
    """
    try:
        user_id = current_user.get('id')
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        async with db_pool.acquire() as conn:
            # Hole alle Domain-Locks des Users
            locks = await conn.fetch(
                """
                SELECT 
                    domain_name,
                    fixes_used,
                    fixes_limit,
                    is_unlocked,
                    created_at,
                    unlocked_at
                FROM domain_locks
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )
            
            # Konvertiere zu Dict-Liste
            domain_locks = [
                {
                    'domain_name': lock['domain_name'],
                    'fixes_used': lock['fixes_used'],
                    'fixes_limit': lock['fixes_limit'],
                    'is_unlocked': lock['is_unlocked'],
                    'created_at': lock['created_at'].isoformat() if lock['created_at'] else None,
                    'unlocked_at': lock['unlocked_at'].isoformat() if lock['unlocked_at'] else None
                }
                for lock in locks
            ]
            
            logger.info(f"User {user_id} has {len(domain_locks)} domain locks")
            
            return {
                "success": True,
                "domain_locks": domain_locks,
                "total": len(domain_locks)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching domain locks: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Laden der Domain-Status: {str(e)}"
        )

@router.get("/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Holt das vollständige User-Profil
    
    Returns:
        User-Profil mit Limits, Plan-Info und Domain-Locks
    """
    try:
        user_id = current_user.get('id')
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        async with db_pool.acquire() as conn:
            # Hole User Limits
            limits = await conn.fetchrow(
                """
                SELECT 
                    plan_type,
                    fixes_used,
                    fixes_limit,
                    websites_max,
                    exports_max,
                    exports_used
                FROM user_limits
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Hole Domain-Locks
            locks = await conn.fetch(
                """
                SELECT 
                    domain_name,
                    fixes_used,
                    fixes_limit,
                    is_unlocked
                FROM domain_locks
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id
            )
            
            # Hole Subscription Status
            subscription = await conn.fetchrow(
                """
                SELECT 
                    plan_type,
                    status,
                    created_at
                FROM subscriptions
                WHERE user_id = $1 AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id
            )
            
            return {
                "success": True,
                "user": {
                    "id": user_id,
                    "email": current_user.get('email'),
                    "full_name": current_user.get('full_name')
                },
                "limits": dict(limits) if limits else None,
                "domain_locks": [dict(lock) for lock in locks],
                "subscription": dict(subscription) if subscription else None,
                "stats": {
                    "total_domains": len(locks),
                    "unlocked_domains": sum(1 for lock in locks if lock['is_unlocked']),
                    "locked_domains": sum(1 for lock in locks if not lock['is_unlocked'])
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Laden des Profils: {str(e)}"
        )

@router.get("/health")
async def user_health():
    """Health check for user service"""
    return {
        "status": "healthy",
        "service": "user",
        "db_pool_initialized": db_pool is not None,
        "auth_service_initialized": auth_service is not None
    }


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    company: Optional[str] = None

class UpdateBillingRequest(BaseModel):
    company_name: Optional[str] = None
    vat_id: Optional[str] = None
    street: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.put("/profile")
async def update_user_profile(request: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with db_pool.acquire() as conn:
            updates = []
            params = []
            idx = 1

            if request.full_name is not None:
                updates.append(f"full_name = ${idx}")
                params.append(request.full_name)
                idx += 1
            if request.company is not None:
                updates.append(f"company = ${idx}")
                params.append(request.company)
                idx += 1

            if not updates:
                return {"success": True, "message": "Keine Aenderungen"}

            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)}, updated_at = NOW() WHERE id = ${idx}"
            await conn.execute(query, *params)

            return {"success": True, "message": "Profil aktualisiert"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern: {str(e)}")


@router.put("/billing")
async def update_billing_data(request: UpdateBillingRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_company_data (user_id, company_name, tax_id, company_address, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    company_name = COALESCE($2, user_company_data.company_name),
                    tax_id = COALESCE($3, user_company_data.tax_id),
                    company_address = COALESCE($4, user_company_data.company_address),
                    updated_at = NOW()
                """,
                user_id,
                request.company_name,
                request.vat_id,
                f"{request.street or ''}\n{request.postal_code or ''} {request.city or ''}\n{request.country or ''}".strip()
            )

            return {"success": True, "message": "Rechnungsdaten gespeichert"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating billing: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern: {str(e)}")


@router.put("/password")
async def change_password(request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    try:
        user_id = current_user.get('id')
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized")

        if len(request.new_password) < 8:
            raise HTTPException(status_code=400, detail="Passwort muss mindestens 8 Zeichen lang sein")

        async with db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT hashed_password FROM users WHERE id = $1", user_id)
            if not user:
                raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")

            if not bcrypt.checkpw(request.current_password.encode('utf-8'), user['hashed_password'].encode('utf-8')):
                raise HTTPException(status_code=400, detail="Aktuelles Passwort ist falsch")

            new_hash = bcrypt.hashpw(request.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            await conn.execute("UPDATE users SET hashed_password = $1, updated_at = NOW() WHERE id = $2", new_hash, user_id)

            return {"success": True, "message": "Passwort erfolgreich geaendert"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Aendern des Passworts: {str(e)}")

