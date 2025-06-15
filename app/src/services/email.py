import os 
import smtplib 
from email.mime.text import MIMEText         
from email.mime.multipart import MIMEMultipart 

from app.src.config.config import settings

def send_verification_email(email_to: str, token: str):
    message = MIMEMultipart("alternative") 
    message["Subject"] = "Verify your email" 
    message["From"] = settings.MAIL_USERNAME 
    message["To"] = email_to

    verify_link = f"http://localhost:8000/auth/verify?token={token}"
    text = f"Hi!\nPlease verify your email by clicking on the link: {verify_link}"
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

    with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
        server.starttls()     
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)    
        server.sendmail(
            settings.MAIL_USERNAME, email_to, message.as_string()   
        )       
