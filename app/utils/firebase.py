"""
Firebase Cloud Messaging — Send push notifications to user devices.
Requires firebase-admin SDK: pip install firebase-admin
"""
from app.config import settings

firebase_app = None


def init_firebase():
    """Initialize Firebase Admin SDK. Call once on startup."""
    global firebase_app
    if not settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        print("Firebase: No service account path configured, FCM disabled")
        return

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        firebase_app = firebase_admin.initialize_app(cred)
        print("Firebase initialized")
    except Exception as e:
        print(f"Firebase init failed: {e}")


async def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None) -> bool:
    """Send push notification via FCM. Returns True on success."""
    if not firebase_app:
        print(f"FCM skipped (not initialized): {title}")
        return False

    try:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
        )
        messaging.send(message)
        return True
    except Exception as e:
        print(f"FCM send failed: {e}")
        return False
