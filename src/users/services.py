import base64
import pyotp
from datetime import timedelta
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.utils.html import strip_tags
from rest_framework_simplejwt.tokens import RefreshToken

from piledesigner.settings import (
    OTP_EXPIRY_TIME_IN_SECONDS,
    DHPD_TOOL_DOMAIN
)
from .models import OTP
from .exceptions import NeedToRequestNewOTP, OTPEmailNotExists, OTPExpiredOrIncorrect

class AuthService:
    @staticmethod
    def authenticate_user(username, password):
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        return user

    @staticmethod
    def generate_tokens(user, remember_me=False):
        refresh = RefreshToken.for_user(user)
        access_token_time = 15
        refresh_token_time = 1

        # Adjust token expiration based on "remember_me" flag
        if remember_me:
            refresh_token_time = 30 # Longer expiration for "Remember Me"
        else:
            refresh_token_time = 1

        refresh.set_exp(lifetime=timedelta(days=refresh_token_time))
        refresh.access_token.set_exp(lifetime=timedelta(minutes=access_token_time))

        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
            "access_token_time": access_token_time,
            "refresh_token_time": refresh_token_time,
        }


class EmailService:
    @staticmethod
    def send_otp_email(email):
        gen_otp = GenOTP.gen_otp(email)

        if not gen_otp:
            raise RuntimeError(f'Failed to generate OTP code for {email}')

        subject = "Bestätigen Sie Ihre E-Mail-Adresse"  # Subject line
    
        # HTML content (as in your image)
        html_content = f"""
        <div style="font-family:Arial,sans-serif; max-width:600px; margin:0 auto">
            <div style="padding-top:20px; text-align:center">
                <img src="https://cdn.piledesigner.io/cdn/files/images/otp_email_logo.png" style="max-width:90px" data-imagetype="External">
            </div>
            <div style="padding-bottom:20px">
                <h2 style="text-align: center; padding-bottom: 20px">Bestätigen Sie Ihre E-Mail-Adresse</h2>
                <p>Ihr Sicherheitscode lautet:</p>
                <div style="background-color:#f0f0f0; padding:5px; margin:20px 0;
                            font-size:24px; letter-spacing:2px; text-align:center">
                    <strong>{str(gen_otp)}</strong>
                </div>
                <p style="text-align: center; margin-bottom:20">Dieser Code ist 10 Minuten gültig.</p>
                <p>Bitte geben Sie den Sicherheitscode in das Fenster ein, in dem Sie mit der Erstellung Ihres Kontos begonnen haben. Geben Sie diesen Code aus Sicherheitsgründen nicht an Dritte weiter.</p>
                <p>Dankeschön.</p>
            </div>
        </div>
        """

        # Plain text content (for email clients that don't support HTML)
        plain_text_content = strip_tags(html_content)  # Remove HTML tags

        send_mail(
            subject,
            plain_text_content,  # Use plain text here
            settings.EMAIL_HOST_USER,  # Replace with your send-from email
            [email],  # List of recipient emails
            fail_silently=False,  # Set to True for testing, False for production
            html_message=html_content,  # Include HTML content for HTML-enabled clients
        )


class GenerateKey:
    """
    Generate and Verify the Key depend on email and Time Unit
    """
    @staticmethod
    def secret_base32(email: str, counter: str):
        """
        Generate the key depend on email
        """
        secret = email + counter
        secret_base32 = base64.b32encode(secret.encode())  # Key is generated
        return secret_base32


class GenOTP:
    """
    Generate and Verify the OTP value depend on Phone and Time Unit
    """
    @staticmethod
    def gen_otp(email: str) -> str:
        """
        Generate OTP from email address

        Attributes:
            email: str

        Return:
            otp: str
        """
        try:
            # if email_model already exists the take this else create new object
            email_otp = OTP.objects.get(email = email)
            email_otp.counter += 1

        except OTP.DoesNotExist:
            OTP.objects.create(email=email)
            email_otp = OTP.objects.get(email = email)  # user Newly created Model

        email_otp.isVerified = False
        email_otp.save()  # Save the data

        key = GenerateKey.secret_base32(email, str(email_otp.counter))

        otp_service = pyotp.TOTP(s=key, interval=OTP_EXPIRY_TIME_IN_SECONDS,)  # TOTP Model

        otp = otp_service.now()

        return otp

    # This Method verifies the OTP
    @staticmethod
    def verify_otp(otp_value: str, email: str):
        """
        Verify OTP from email address

        Attributes:
            otp: str
            email: str

        """

        # Make sure we have one object for this email first
        try:
            email_otp = OTP.objects.get(email = email)

        # Fail early if there's no verification attempt
        except OTP.DoesNotExist:
            raise OTPEmailNotExists

        # And make sure this email has not been verified before
        if email_otp.isVerified:
            raise NeedToRequestNewOTP

        key = GenerateKey.secret_base32(email, str(email_otp.counter))
        otp_service = pyotp.TOTP(s=key, interval=OTP_EXPIRY_TIME_IN_SECONDS)

        if otp_service.verify(otp=otp_value,):
            email_otp.isVerified = True
            email_otp.save()
        else:
            raise OTPExpiredOrIncorrect
