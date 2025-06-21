import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.src.config.config import settings
import logging
from pathlib import Path
from datetime import datetime, timedelta
import jwt
from typing import Optional
from functools import lru_cache 
from email_validator import validate_email, EmailNotValidError

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
    """
    try:
        # Валідація email
        if not settings.mail_test_mode:
            try:
                valid = validate_email(email_to)
                email_to = valid.email
            except EmailNotValidError as e:
                logger.error(f"Invalid email: {str(e)}")
                return False 

        # Перенаправлення для тестів
        if settings.mail_test_mode:  
            email_to = settings.mail_test_recipient  
            logger.info(f"Test mode active. Redirecting email to {email_to}")  

        # Завантаження шаблону
        try:  
            html_content = load_template(template_name)  
        except Exception as e:  
            logger.error(f"Failed to load template {template_name}: {str(e)}") 
            return False  
        # Заміна плейсхолдерів
        for key, value in template_vars.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

        # Підготовка повідомлення
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

        # Відправка
        with smtplib.SMTP(**smtp_params) as server:
            if settings.mail_starttls:
                server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            server.send_message(msg)
        
        logger.info(f"Email successfully sent to {email_to}")  
        return True 

    except smtplib.SMTPException as e:  
        logger.error(f"SMTP error occurred: {str(e)}")  
    except ssl.SSLError as e: 
        logger.error(f"SSL error occurred: {str(e)}")  
    except Exception as e:  
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)  
    
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

@lru_cache(maxsize=32)
def load_template(template_name: str) -> str:
    """Завантажує і кешує HTML шаблон."""
    template_path = Path(__file__).parent / "templates" / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    with open(template_path, "r", encoding="utf-8") as file:
        return file.read()