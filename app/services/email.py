"""
Email service for sending verification and notification emails.
"""

import secrets
from typing import Optional
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, BaseLoader
from app.config import settings


# Email templates
EMAIL_VERIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Xác thực Email - VHealth</title>
    <link rel="icon" type="image/png" href="https://storage.googleapis.com/vhealth-dev-public/favicon.png" />
    <style>
      /* Reset and base styles */
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }

      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
          Oxygen, Ubuntu, Cantarell, sans-serif;
        line-height: 1.6;
        color: #1a1a1a;
        background-color: #f8f9fa;
        margin: 0;
        padding: 0;
        -webkit-text-size-adjust: 100%;
        -ms-text-size-adjust: 100%;
      }

      /* Container */
      .email-container {
        max-width: 600px;
        margin: 0 auto;
        background-color: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
          0 2px 4px -1px rgba(0, 0, 0, 0.06);
      }

      /* Header */
      .header {
        background: linear-gradient(135deg, #00bba7 0%, #00bc7d 100%);
        padding: 32px 40px;
        text-align: center;
      }

      .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 8px;
      }

      .logo-image {
        width: 40px;
        height: 40px;
        display: block;
      }

      .logo {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.025em;
        margin: 0;
      }

      .tagline {
        color: rgba(255, 255, 255, 0.9);
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 0.025em;
        text-transform: uppercase;
      }

      /* Content */
      .content {
        padding: 40px;
      }

      .content h1 {
        font-size: 24px;
        font-weight: 700;
        color: #101828;
        margin-bottom: 24px;
        letter-spacing: -0.025em;
        line-height: 1.3;
      }

      .greeting {
        font-size: 16px;
        color: #374151;
        margin-bottom: 20px;
        font-weight: 500;
      }

      .content p {
        font-size: 16px;
        color: #6a7282;
        margin-bottom: 20px;
        line-height: 1.7;
      }

      /* Button */
      .button-container {
        text-align: center;
        margin: 32px 0;
      }

      .button {
        display: inline-block;
        padding: 16px 32px;
        background: linear-gradient(135deg, #00bba7 0%, #00bc7d 100%);
        color: #ffffff;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        letter-spacing: 0.025em;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 187, 167, 0.3);
      }

      .button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 8px -1px rgba(0, 187, 167, 0.4);
      }

      /* Unified info box styles */
      .info-box {
        background-color: #f8f9fa;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        margin: 20px 0;
      }

      .info-box p {
        font-size: 14px;
        color: #374151;
        margin: 0;
        line-height: 1.6;
      }

      .info-box p + p {
        margin-top: 8px;
      }

      .info-box strong {
        color: #101828;
        font-weight: 600;
      }

      .info-box a {
        color: #00bba7;
        word-break: break-all;
        text-decoration: none;
      }

      .info-box a:hover {
        text-decoration: underline;
      }

      /* Link fallback - uses base info-box style */
      .link-fallback {
        background-color: #f8f9fa;
        border-color: #e5e7eb;
      }

      /* Warning box - uses base info-box style */
      .warning {
        background-color: #f8f9fa;
        border-color: #e5e7eb;
      }

      /* Security notice - uses base info-box style */
      .security-notice {
        background-color: #f8f9fa;
        border-color: #e5e7eb;
      }

      /* Footer */
      .footer {
        background-color: #f8f9fa;
        padding: 32px 40px;
        border-top: 1px solid #e5e7eb;
        text-align: center;
      }

      .footer p {
        font-size: 12px;
        color: #657282;
        margin: 0;
        line-height: 1.5;
      }

      .footer a {
        color: #00bba7;
        text-decoration: none;
      }

      .footer a:hover {
        text-decoration: underline;
      }

      /* Responsive design */
      @media only screen and (max-width: 600px) {
        .email-container {
          margin: 0;
          border-radius: 0;
        }

        .header,
        .content,
        .footer {
          padding: 24px 20px;
        }

        .logo-container {
          flex-direction: column;
          gap: 8px;
        }

        .logo-image {
          width: 32px;
          height: 32px;
        }

        .logo {
          font-size: 24px;
        }

        .content h1 {
          font-size: 20px;
        }

        .button {
          padding: 14px 24px;
          font-size: 15px;
        }
      }

      /* Dark mode support */
      @media (prefers-color-scheme: dark) {
        body {
          background-color: #111827;
        }

        .email-container {
          background-color: #1f2937;
        }

        .content h1 {
          color: #f9fafb;
        }

        .greeting {
          color: #d1d5db;
        }

        .content p {
          color: #9ca3af;
        }

        .footer {
          background-color: #111827;
          border-top-color: #374151;
        }

        .footer p {
          color: #9ca3af;
        }
      }
    </style>
  </head>
  <body>
    <div style="padding: 20px 0">
      <div class="email-container">
        <!-- Header -->
        <div class="header">
          <div class="logo-container">
            <img src="https://storage.googleapis.com/vhealth-dev-public/favicon.png" alt="VHealth Logo" class="logo-image" style="display:block; width:40px; height:40px;" width="40" height="40" />
            <div class="logo">VHealth</div>
          </div>
          <div class="tagline">Quản lý sức khỏe thông minh</div>
        </div>

        <!-- Content -->
        <div class="content">
          <h1>Chào mừng, {{ first_name }}!</h1>

          <div class="greeting">Xin chào {{ first_name }},</div>

          <p>
            Cảm ơn bạn đã đăng ký tài khoản với VHealth. Vui lòng xác thực địa chỉ email
            bằng cách nhấp vào nút bên dưới:
          </p>

          <div class="button-container">
            <a href="{{ verification_url }}" class="button" role="button"
              >Xác thực Email</a
            >
          </div>

          <div class="info-box link-fallback">
            <p>
              <strong>Nút không hoạt động?</strong> Sao chép và dán liên kết sau vào trình duyệt:
            </p>
            <p>
              <a href="{{ verification_url }}">{{ verification_url }}</a>
            </p>
          </div>

          <div class="info-box warning">
            <p>
              Liên kết xác thực này sẽ hết hạn sau {{ expiry_minutes }} phút.
            </p>
          </div>

          <div class="info-box security-notice">
            <p>
              <strong>Thông báo bảo mật:</strong> Nếu bạn không tạo tài khoản
              với chúng tôi, vui lòng bỏ qua email này. Tài khoản của bạn vẫn an toàn và không có thay đổi nào được thực hiện.
            </p>
          </div>

          <p>
            Cần hỗ trợ? Liên hệ với chúng tôi tại
            <a href="mailto:support@vhealth.io.vn" style="color: #00bba7"
              >support@vhealth.io.vn</a
            >
          </p>
        </div>

        <!-- Footer -->
        <div class="footer">
          <p>
            Đây là email tự động từ VHealth.<br />
            Vui lòng không trả lời email này.
          </p>
          <p style="margin-top: 16px; font-size: 11px; color: #95a1af">
            VHealth | © 2025 Bản quyền thuộc về VHealth
          </p>
        </div>
      </div>
    </div>
  </body>
</html>
"""

# Password reset template
PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Đặt lại Mật khẩu - VHealth</title>
    <link rel="icon" type="image/png" href="https://storage.googleapis.com/vhealth-dev-public/favicon.png" />
    <style>
      /* Reset and base styles */
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }

      body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
          Oxygen, Ubuntu, Cantarell, sans-serif;
        line-height: 1.6;
        color: #1a1a1a;
        background-color: #f8f9fa;
        margin: 0;
        padding: 0;
        -webkit-text-size-adjust: 100%;
        -ms-text-size-adjust: 100%;
      }

      /* Container */
      .email-container {
        max-width: 600px;
        margin: 0 auto;
        background-color: #ffffff;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1),
          0 2px 4px -1px rgba(0, 0, 0, 0.06);
      }

      /* Header */
      .header {
        background: linear-gradient(135deg, #00bba7 0%, #00bc7d 100%);
        padding: 32px 40px;
        text-align: center;
      }

      .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 8px;
      }

      .logo-image {
        width: 40px;
        height: 40px;
        display: block;
      }

      .logo {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.025em;
        margin: 0;
      }

      .tagline {
        color: rgba(255, 255, 255, 0.9);
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 0.025em;
        text-transform: uppercase;
      }

      /* Content */
      .content {
        padding: 40px;
      }

      .content h1 {
        font-size: 24px;
        font-weight: 700;
        color: #101828;
        margin-bottom: 24px;
        letter-spacing: -0.025em;
        line-height: 1.3;
      }

      .greeting {
        font-size: 16px;
        color: #374151;
        margin-bottom: 20px;
        font-weight: 500;
      }

      .content p {
        font-size: 16px;
        color: #6a7282;
        margin-bottom: 20px;
        line-height: 1.7;
      }

      /* Button */
      .button-container {
        text-align: center;
        margin: 32px 0;
      }

      .button {
        display: inline-block;
        padding: 16px 32px;
        background: linear-gradient(135deg, #00bba7 0%, #00bc7d 100%);
        color: #ffffff;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        letter-spacing: 0.025em;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 187, 167, 0.3);
      }

      .button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 8px -1px rgba(0, 187, 167, 0.4);
      }

      /* Unified info box styles */
      .info-box {
        background-color: #f8f9fa;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 16px;
        margin: 20px 0;
      }

      .info-box p {
        font-size: 14px;
        color: #374151;
        margin: 0;
        line-height: 1.6;
      }

      .info-box p + p {
        margin-top: 8px;
      }

      .info-box strong {
        color: #101828;
        font-weight: 600;
      }

      .info-box a {
        color: #00bba7;
        word-break: break-all;
        text-decoration: none;
      }

      .info-box a:hover {
        text-decoration: underline;
      }

      /* Link fallback - uses base info-box style */
      .link-fallback {
        background-color: #f8f9fa;
        border-color: #e5e7eb;
      }

      /* Warning box - uses base info-box style */
      .warning {
        background-color: #f8f9fa;
        border-color: #e5e7eb;
      }

      /* Security notice - uses base info-box style */
      .security-notice {
        background-color: #f8f9fa;
        border-color: #e5e7eb;
      }

      /* Footer */
      .footer {
        background-color: #f8f9fa;
        padding: 32px 40px;
        border-top: 1px solid #e5e7eb;
        text-align: center;
      }

      .footer p {
        font-size: 12px;
        color: #657282;
        margin: 0;
        line-height: 1.5;
      }

      .footer a {
        color: #00bba7;
        text-decoration: none;
      }

      .footer a:hover {
        text-decoration: underline;
      }

      /* Responsive design */
      @media only screen and (max-width: 600px) {
        .email-container {
          margin: 0;
          border-radius: 0;
        }

        .header,
        .content,
        .footer {
          padding: 24px 20px;
        }

        .logo-container {
          flex-direction: column;
          gap: 8px;
        }

        .logo-image {
          width: 32px;
          height: 32px;
        }

        .logo {
          font-size: 24px;
        }

        .content h1 {
          font-size: 20px;
        }

        .button {
          padding: 14px 24px;
          font-size: 15px;
        }
      }

      /* Dark mode support */
      @media (prefers-color-scheme: dark) {
        body {
          background-color: #111827;
        }

        .email-container {
          background-color: #1f2937;
        }

        .content h1 {
          color: #f9fafb;
        }

        .greeting {
          color: #d1d5db;
        }

        .content p {
          color: #9ca3af;
        }

        .footer {
          background-color: #111827;
          border-top-color: #374151;
        }

        .footer p {
          color: #9ca3af;
        }
      }
    </style>
  </head>
  <body>
    <div style="padding: 20px 0">
      <div class="email-container">
        <!-- Header -->
        <div class="header">
          <div class="logo-container">
            <img src="https://storage.googleapis.com/vhealth-dev-public/favicon.png" alt="VHealth Logo" class="logo-image" style="display:block; width:40px; height:40px;" width="40" height="40" />
            <div class="logo">VHealth</div>
          </div>
          <div class="tagline">Quản lý sức khỏe thông minh</div>
        </div>

        <!-- Content -->
        <div class="content">
          <h1>Yêu cầu Đặt lại Mật khẩu</h1>

          <div class="greeting">Xin chào {{ first_name }},</div>

          <p>
            Chúng tôi đã nhận được yêu cầu đặt lại mật khẩu cho tài khoản VHealth của bạn.
            Nhấp vào nút bên dưới để đặt lại mật khẩu:
          </p>

          <div class="button-container">
            <a href="{{ reset_url }}" class="button" role="button"
              >Đặt lại Mật khẩu</a
            >
          </div>

          <div class="info-box link-fallback">
            <p>
              <strong>Nút không hoạt động?</strong> Vui lòng liên hệ với đội ngũ hỗ trợ
              để được hỗ trợ đặt lại mật khẩu.
            </p>
          </div>

          <div class="info-box warning">
            <p>
              Liên kết đặt lại này sẽ hết hạn sau {{ expiry_minutes }} phút.
            </p>
          </div>

          <div class="info-box security-notice">
            <p>
              <strong>Thông báo bảo mật:</strong> Nếu bạn không yêu cầu đặt lại
              mật khẩu này, vui lòng bỏ qua email này. Mật khẩu của bạn sẽ không thay đổi và tài khoản của bạn vẫn an toàn.
            </p>
          </div>

          <p>
            Cần hỗ trợ? Liên hệ với chúng tôi tại
            <a href="mailto:support@vhealth.io.vn" style="color: #00bba7"
              >support@vhealth.io.vn</a
            >
          </p>
        </div>

        <!-- Footer -->
        <div class="footer">
          <p>
            Đây là email bảo mật tự động từ VHealth.<br />
            Vui lòng không trả lời email này.
          </p>
          <p style="margin-top: 16px; font-size: 11px; color: #95a1af">
            VHealth | © 2025 Bản quyền thuộc về VHealth
          </p>
        </div>
      </div>
    </div>
  </body>
</html>
"""


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        if not self._is_configured():
            self.mail = None
            return

        # Configure FastMail
        conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from,
            MAIL_PORT=settings.mail_port,
            MAIL_SERVER=settings.mail_server,
            MAIL_STARTTLS=settings.mail_tls,
            MAIL_SSL_TLS=settings.mail_ssl,
            USE_CREDENTIALS=settings.use_credentials,
            VALIDATE_CERTS=settings.validate_certs,
        )
        self.mail = FastMail(conf)
        self.template_env = Environment(loader=BaseLoader())

    def _is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return all(
            [
                settings.mail_username,
                settings.mail_password,
                settings.mail_from,
                settings.mail_server,
            ]
        )

    def _render_template(self, template: str, **context) -> str:
        """Render email template with context."""
        template_obj = self.template_env.from_string(template)
        return template_obj.render(**context)

    async def send_email_verification(
        self,
        email: str,
        first_name: str,
        verification_token: str,
        base_url: str = "http://localhost:3000",
    ) -> bool:
        """Send email verification email."""
        if not self.mail:
            print(
                f"Email service not configured. Verification token for {email}: {verification_token}"
            )
            return False

        try:
            verification_url = (
                f"{base_url}/auth/verify-email?token={verification_token}"
            )

            html_content = self._render_template(
                EMAIL_VERIFICATION_TEMPLATE,
                first_name=first_name,
                verification_url=verification_url,
                expiry_minutes=settings.email_verification_expire_minutes,
            )

            message = MessageSchema(
                subject="Verify Your Email - Health Management",
                recipients=[email],
                body=html_content,
                subtype="html",
            )

            await self.mail.send_message(message)
            return True

        except Exception as e:
            print(f"Failed to send email verification to {email}: {e}")
            return False

    async def send_password_reset(
        self,
        email: str,
        first_name: str,
        reset_token: str,
        base_url: str = "http://localhost:3000",
    ) -> bool:
        """Send password reset email."""
        if not self.mail:
            print(
                f"Email service not configured. Password reset token for {email}: {reset_token}"
            )
            return False

        try:
            reset_url = f"{base_url}/auth/reset-password?token={reset_token}"

            html_content = self._render_template(
                PASSWORD_RESET_TEMPLATE,
                first_name=first_name,
                reset_url=reset_url,
                expiry_minutes=settings.password_reset_expire_minutes,
            )

            message = MessageSchema(
                subject="Password Reset - Health Management",
                recipients=[email],
                body=html_content,
                subtype="html",
            )

            await self.mail.send_message(message)
            return True

        except Exception as e:
            print(f"Failed to send password reset email to {email}: {e}")
            return False

    def generate_verification_token(self) -> str:
        """Generate a secure verification token."""
        return secrets.token_urlsafe(32)

    def generate_reset_token(self) -> str:
        """Generate a secure password reset token."""
        return secrets.token_urlsafe(32)


# Global email service instance
email_service = EmailService()
