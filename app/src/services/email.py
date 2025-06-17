import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from app.src.config.config import settings

async def send_verification_email(email_to: str, token: str):
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify your email"
        message["From"] = settings.mail_from
        message["To"] = email_to

        verify_link = f"http://localhost:8000/auth/verify?token={token}"
        
        text = f"""Hi!
Please verify your email by clicking on the link: {verify_link}"""
        
        html = f"""
        <html>
            <body>
                <p>Hi!<br>
                    Please verify your email by clicking the link below:<br>
                    <a href="{verify_link}">Verify Email</a>
                </p>
            </body>
        </html>
        """
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            if settings.mail_starttls:
                server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            server.send_message(message)
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {str(e)}"
        )