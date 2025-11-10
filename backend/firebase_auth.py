"""
Firebase Admin SDK Integration für Backend Token Verification
"""
import os
from typing import Optional, Dict
from firebase_admin import credentials, auth, initialize_app
from fastapi import HTTPException, status

# Firebase App Initialization (nur einmal)
_firebase_app = None

def init_firebase_admin():
    """Initialize Firebase Admin SDK with service account credentials"""
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    try:
        # Service Account Config aus Environment Variables
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
        
        # Validate required fields
        if not all([
            firebase_config["project_id"],
            firebase_config["private_key"],
            firebase_config["client_email"]
        ]):

            return None
        
        cred = credentials.Certificate(firebase_config)
        _firebase_app = initialize_app(cred)

        return _firebase_app
        
    except Exception as e:
        print(f"⚠️ Firebase Admin SDK initialization failed: {e}")
        return None

async def verify_firebase_token(id_token: str) -> Dict:
    """
    Verify Firebase ID token and return user data
    
    Args:
        id_token: Firebase ID token from frontend
        
    Returns:
        dict: User data from Firebase (uid, email, name, email_verified)
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if _firebase_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Auth is not configured"
        )
    
    try:
        # Verify token with Firebase Admin SDK
        decoded_token = auth.verify_id_token(id_token)
        
        # Extract user data
        user_data = {
            'firebase_uid': decoded_token['uid'],
            'email': decoded_token.get('email'),
            'name': decoded_token.get('name'),
            'picture': decoded_token.get('picture'),
            'email_verified': decoded_token.get('email_verified', False),
            'provider': decoded_token.get('firebase', {}).get('sign_in_provider', 'unknown')
        }
        
        return user_data
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token expired"
        )
    except auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token revoked"
        )
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token"
        )
    except Exception as e:
        print(f"Firebase token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )

async def get_firebase_user(uid: str) -> Optional[Dict]:
    """
    Get Firebase user by UID
    
    Args:
        uid: Firebase user UID
        
    Returns:
        dict: User data or None if not found
    """
    if _firebase_app is None:
        return None
    
    try:
        user = auth.get_user(uid)
        return {
            'firebase_uid': user.uid,
            'email': user.email,
            'name': user.display_name,
            'picture': user.photo_url,
            'email_verified': user.email_verified,
            'disabled': user.disabled
        }
    except auth.UserNotFoundError:
        return None
    except Exception as e:
        print(f"Error getting Firebase user: {e}")
        return None

