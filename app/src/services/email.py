import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from app.src.config.config import settings
from ssl import SSLError

async def send_verification_email(email_to: str, token: str):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify your email"
        message["From"] = settings.mail_from
        message["To"] = email_to

        verify_link = f"{settings.frontend_url}/auth/verify?token={token}"  

        html = f"""
        <html>
            <body>
                <p>Hi!<br>Please verify your email:</p>
                <a href="{verify_link}">Click here</a>
                <p>Link expires in 24 hours.</p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            server.ehlo()
            if settings.mail_starttls:
                server.starttls()
                server.ehlo()
            server.login(settings.mail_username, settings.mail_password)
            server.send_message(message)
                
    except SSLError as e:
        raise HTTPException(status_code=500, detail=f"SSL error: {e}")
    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=500, detail="SMTP authentication failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email sending failed: {e}")