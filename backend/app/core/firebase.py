"""
Firebase Admin SDK initialization and token verification.
"""

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials


def init_firebase():
    """Initialize Firebase Admin SDK.

    Uses Application Default Credentials when GOOGLE_APPLICATION_CREDENTIALS
    env var is set, otherwise initializes with no credentials (for development
    with Firebase Auth emulator).
    """
    if not firebase_admin._apps:
        try:
            # Try Application Default Credentials first
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        except Exception:
            # Fallback: initialize without credentials (works with emulator
            # or when project ID is set via GCLOUD_PROJECT env var)
            firebase_admin.initialize_app()


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return the decoded claims.

    Args:
        id_token: The Firebase ID token string from the client.

    Returns:
        dict with keys: uid, email, name, etc.

    Raises:
        firebase_admin.auth.InvalidIdTokenError: If token is invalid.
        firebase_admin.auth.ExpiredIdTokenError: If token is expired.
    """
    return firebase_auth.verify_id_token(id_token)
