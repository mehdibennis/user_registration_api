import logging

from src.domain.ports import EmailService

logger = logging.getLogger(__name__)


class ConsoleEmailService(EmailService):
    async def send_activation_code(self, email: str, code: str) -> None:
        # In a real scenario, this would make an HTTP call to a 3rd party SMTP service
        # or use an SMTP library to send the email.
        # For this exercise, we print to console as allowed by specs.
        print(f"==================================================")
        print(f"EMAIL TO: {email}")
        print(f"SUBJECT: Activate your account")
        print(f"BODY: Your activation code is: {code}")
        print(f"==================================================")
        logger.info(f"Sent activation code {code} to {email}")
