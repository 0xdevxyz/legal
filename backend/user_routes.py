"""
User Routes - User Profile & Domain Locks
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict
import logging

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

