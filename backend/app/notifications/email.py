import abc
import logging
from email.message import EmailMessage
import aiosmtplib
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailProvider(abc.ABC):
    @abc.abstractmethod
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        pass

class ConsoleEmailProvider(EmailProvider):
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        print("\n" + "="*50)
        print("                 EMAIL SIMULATION")
        print("="*50)
        print(f"TO: {to_email}")
        print(f"SUBJECT: {subject}")
        print("-" * 50)
        # In a real environment, we would log this. We just print to console for dev.
        # We don't print the full HTML to avoid overwhelming the log, just a summary snippet.
        print(f"BODY (First 200 chars):\n{html_content[:200]}...")
        print("="*50 + "\n")
        logger.info(f"Simulated sending email to {to_email} with subject '{subject}'")
        return True

class SMTPEmailProvider(EmailProvider):
    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        if not settings.SMTP_HOST:
            logger.error("SMTP_HOST is not configured")
            return False
            
        message = EmailMessage()
        message["From"] = settings.SMTP_FROM
        message["To"] = to_email
        message["Subject"] = subject
        message.add_alternative(html_content, subtype='html')

        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                use_tls=settings.SMTP_USE_TLS,
                start_tls=not settings.SMTP_USE_TLS, # typically if use_tls is false we want start_tls
                timeout=10
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

def get_email_provider() -> EmailProvider:
    if settings.EMAIL_ENABLED:
        return SMTPEmailProvider()
    return ConsoleEmailProvider()

# Basic Email Template Builder
def build_email_html(title: str, summary: str, details: dict, link: str = None) -> str:
    """
    Builds a secure HTML email template without exposing raw events.
    """
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px; color: #18181b;">
            <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; border: 1px solid #e4e4e7;">
                <div style="background-color: #18181b; padding: 20px; color: white;">
                    <h2 style="margin: 0;">SentinelSOC</h2>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #a1a1aa;">Security Operations Center</p>
                </div>
                <div style="padding: 20px;">
                    <h3 style="margin-top: 0; color: #18181b;">{title}</h3>
                    <p style="color: #3f3f46; line-height: 1.5;">{summary}</p>
                    
                    <div style="background-color: #f4f4f5; padding: 15px; border-radius: 6px; margin: 20px 0;">
    """
    
    for key, value in details.items():
        if value:
            html += f'<div style="margin-bottom: 8px;"><strong style="color: #52525b;">{key}:</strong> {value}</div>'
            
    html += """
                    </div>
    """
    
    if link:
        html += f"""
                    <div style="margin-top: 30px; text-align: center;">
                        <a href="{link}" style="background-color: #2563eb; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; display: inline-block;">Open in SentinelSOC</a>
                    </div>
        """
        
    html += """
                </div>
                <div style="background-color: #fafafa; padding: 15px; text-align: center; border-top: 1px solid #e4e4e7; font-size: 12px; color: #71717a;">
                    This is an automated notification from SentinelSOC. Please do not reply.
                </div>
            </div>
        </body>
    </html>
    """
    return html
