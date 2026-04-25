"""
Email service – sends transactional emails via SMTP (async).
Handles welcome emails, notifications, and template-based sending.
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger("auragrowth")

# ── Welcome Email Template ───────────────────────────────────────────────

WELCOME_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #f4f7fa; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; }
        .header h1 { color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; }
        .header p { color: rgba(255,255,255,0.9); margin-top: 8px; font-size: 16px; }
        .body { padding: 40px 30px; }
        .body h2 { color: #2d3748; font-size: 22px; margin-top: 0; }
        .body p { color: #4a5568; line-height: 1.7; font-size: 15px; }
        .steps { background: #f7fafc; border-radius: 8px; padding: 24px; margin: 24px 0; }
        .step { display: flex; align-items: flex-start; margin-bottom: 16px; }
        .step-num { background: #667eea; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; margin-right: 14px; margin-top: 2px; }
        .step-text { color: #4a5568; font-size: 14px; line-height: 1.6; }
        .cta { text-align: center; margin: 32px 0; }
        .cta a { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 14px 36px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 16px; display: inline-block; }
        .footer { background: #f7fafc; padding: 24px 30px; text-align: center; border-top: 1px solid #e2e8f0; }
        .footer p { color: #a0aec0; font-size: 13px; margin: 4px 0; }
        .footer a { color: #667eea; text-decoration: none; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to AuraGrowth! 🎉</h1>
            <p>Your growth journey starts now</p>
        </div>
        <div class="body">
            <h2>Hey {{ name }}!</h2>
            <p>Thank you for joining AuraGrowth! We're thrilled to have you on board. Our platform is designed to help you automate your communication, grow your audience, and convert leads effortlessly.</p>

            <div class="steps">
                <div class="step">
                    <div class="step-num">1</div>
                    <div class="step-text"><strong>Create your Bio Page</strong> – Set up your personalized link-in-bio page and share all your important links in one place.</div>
                </div>
                <div class="step">
                    <div class="step-num">2</div>
                    <div class="step-text"><strong>Connect your Accounts</strong> – Link your Gmail and Instagram accounts to unlock powerful automation features.</div>
                </div>
                <div class="step">
                    <div class="step-num">3</div>
                    <div class="step-text"><strong>Set up Automations</strong> – Create keyword-triggered Instagram DM automations and email auto-replies to engage your audience 24/7.</div>
                </div>
                <div class="step">
                    <div class="step-num">4</div>
                    <div class="step-text"><strong>Track & Optimize</strong> – Monitor your analytics dashboard to see engagement, clicks, and automation performance in real-time.</div>
                </div>
            </div>

            <div class="cta">
                <a href="https://auragrowth.com/dashboard">Go to Dashboard →</a>
            </div>

            <p>If you have any questions, feel free to reply to this email or reach out to our support team. We're here to help!</p>
        </div>
        <div class="footer">
            <p>© 2025 AuraGrowth. All rights reserved.</p>
            <p>Need help? <a href="mailto:support@auragrowth.com">support@auragrowth.com</a></p>
        </div>
    </div>
</body>
</html>
"""


async def send_email(
    to_email: str,
    subject: str,
    html_body: str,
    text_body: str | None = None,
) -> bool:
    """
    Send an email via SMTP asynchronously.
    Returns True on success, False on failure.
    """
    try:
        message = MIMEMultipart("alternative")
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject

        if text_body:
            message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=settings.SMTP_USE_TLS,
            start_tls=True if settings.SMTP_PORT == 587 else False,
        )

        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


async def send_welcome_email(name: str, email: str) -> bool:
    """
    Send a welcome email to a newly registered user.
    Called as a background task after registration.
    """
    template = Template(WELCOME_EMAIL_TEMPLATE)
    html_body = template.render(name=name)

    return await send_email(
        to_email=email,
        subject="Welcome to AuraGrowth! 🎉",
        html_body=html_body,
        text_body=f"Hey {name}! Welcome to AuraGrowth. Start by creating your bio page and connecting your accounts.",
    )


async def send_template_email(
    to_email: str,
    subject: str,
    template_str: str,
    context: dict,
) -> bool:
    """Send an email using a Jinja2 template string with context variables."""
    template = Template(template_str)
    html_body = template.render(**context)
    return await send_email(to_email=to_email, subject=subject, html_body=html_body)
