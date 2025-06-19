import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.src.config.config import settings
import logging
from pathlib import Path
from datetime import datetime, timedelta
import jwt
from typing import Optional

logger = logging.getLogger(__name__)

def create_verification_token(user_id: int) -> str:
    """
    Генерує JWT токен для верифікації email.    
    Термін дії: 24 години. 
    """     
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "email_verification"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

async def send_email(
    email_to: str,
    subject: str,
    template_name: str,
    template_vars: dict,    
    smtp_timeout: int = 10
) -> bool:  
    """
    Універсальна функція для відправки email.
    
    :param email_to: Отримувач
    :param subject: Тема листа
    :param template_name: Назва HTML шаблону
    :param template_vars: Словник зі змінними для шаблону
    :param smtp_timeout: Таймаут підключення до SMTP
    :return: Статус відправки (True/False)
    """     
    try:
        # Завантажуємо HTML шаблон
        template_path = Path(__file__).parent / "templates" / template_name
        with open(template_path, "r", encoding="utf-8") as file:
            html_content = file.read()
        
        # Замінюємо плейсхолдери
        for key, value in template_vars.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

        # Створюємо повідомлення
        msg = MIMEMultipart()
        msg["From"] = settings.mail_from
        msg["To"] = email_to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        # Налаштування SMTP
        smtp_params = {
            "host": settings.mail_server,
            "port": settings.mail_port,
            "timeout": smtp_timeout
        }

        # Відправка з підтримкою SSL/TLS
        with smtplib.SMTP(**smtp_params) as server:
            if settings.mail_starttls:
                server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            server.send_message(msg)
        
        logger.info(f"Email sent to {email_to} | Subject: {subject}")
        return True 

    except Exception as e:
        logger.error(f"Failed to send email to {email_to}: {str(e)}", exc_info=True)
        return False    
        
async def send_verification_email(email: str, user_id: int) -> bool:
    """ 
    Надсилає email з посиланням для верифікації.
    """
    token = create_verification_token(user_id)
    verification_link = f"{settings.frontend_url}/verify-email?token={token}"
    
    return await send_email(
        email_to=email,
        subject="Підтвердження email у системі GOIT",
        template_name="verification_email.html",
        template_vars={
            "verification_link": verification_link,
            "support_email": "support@goit.com"
        }
    )
    
async def send_password_reset_email(email: str, reset_token: str) -> bool:
    """
    Надсилає email з посиланням для скидання паролю.
    
    :param email: Email користувача
    :param reset_token: Токен для скидання паролю
    :return: Статус відправки (True/False)
    """
    reset_link = f"{settings.frontend_url}/reset-password?token={reset_token}"
    
    return await send_email(
        email_to=email,
        subject="Відновлення паролю GOIT",
        template_name="reset_password.html",
        template_vars={
            "reset_link": reset_link,
            "expires_in": "24 години",  
            "support_contact": settings.mail_from
        }
    )
    
def create_password_reset_token(email: str) -> str:
    """
    Генерує JWT токен для скидання паролю.
    Термін дії: 24 години.
    """
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "type": "password_reset"
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)