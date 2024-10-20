import smtplib
import re
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class MailServiceManager:

    def __init__(
        self, 
        account: str, 
        app_number: str,
    ):
        self._account = account
        self.logger = logging.getLogger("uvicorn")
        self.logger.setLevel(logging.INFO)
        
        self.smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        self.smtp.login(account, app_number)

    def login(self, account, app_number):
        self.smtp.login(account, app_number)

    def send_email(self, msg: MIMEMultipart):
        reg = "^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$"
        address: str = msg.get("To")

        try:
            self.smtp.sendmail(self._account, address, msg.as_string())
            self.logger.info(f"{address} -> Mail send is successful.")
        except Exception as e:
            self.logger.error(f"{address} -> Mail send was failed. Error is {e}")
    
    def build_email(self, address: str, content: str):
        msg = MIMEMultipart()
        msg["Subject"] = "회의록"
        msg["From"] = self._account
        msg["To"] = address
        
        content_part = MIMEText(content, "plain")
        msg.attach(content_part)

        return msg
