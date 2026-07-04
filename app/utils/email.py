import resend
import random
import string
from app.config import settings

resend.api_key = settings.RESEND_API_KEY


def generate_otp(length: int = 6) -> str:
    return "".join(random.choices(string.digits, k=length))


async def send_otp_email(email: str, otp: str, otp_type: str) -> bool:
    if otp_type == "email_verification":
        subject = "Verify your Health Coach account"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
            <h2 style="color: #2d6a4f;">AI Health Coach</h2>
            <p>Your email verification code is:</p>
            <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px;
                        color: #2d6a4f; padding: 16px; background: #f0fdf4;
                        border-radius: 8px; text-align: center;">
                {otp}
            </div>
            <p style="color: #666; font-size: 14px;">
                This code expires in <strong>10 minutes</strong>.
                Do not share it with anyone.
            </p>
        </div>
        """
    else:
        subject = "Reset your Health Coach password"
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto;">
            <h2 style="color: #2d6a4f;">AI Health Coach</h2>
            <p>Your password reset code is:</p>
            <div style="font-size: 36px; font-weight: bold; letter-spacing: 8px;
                        color: #2d6a4f; padding: 16px; background: #f0fdf4;
                        border-radius: 8px; text-align: center;">
                {otp}
            </div>
            <p style="color: #666; font-size: 14px;">
                This code expires in <strong>10 minutes</strong>.
                If you didn't request this, ignore this email.
            </p>
        </div>
        """

    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": email,
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False
