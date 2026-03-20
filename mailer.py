"""
Email delivery to Kindle
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path

logger = logging.getLogger(__name__)


class KindleMailer:
    """Send EPUB files to Kindle via email"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
    
    def send_to_kindle(
        self,
        kindle_email: str,
        epub_path: Path,
        article_title: str
    ) -> bool:
        """
        Send EPUB to Kindle email address
        
        Args:
            kindle_email: Recipient Kindle email address
            epub_path: Path to EPUB file
            article_title: Title for email subject
        
        Returns: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = kindle_email
            msg['Subject'] = f"Article: {article_title}"
            
            # Add body
            body = f"Your article '{article_title}' is attached."
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach EPUB file
            with open(epub_path, 'rb') as f:
                part = MIMEBase('application', 'epub+zip')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename="{epub_path.name}"'
                )
                msg.attach(part)
            
            # Check file size (Amazon limit is 50MB)
            file_size = epub_path.stat().st_size
            if file_size > 50 * 1024 * 1024:
                logger.error(f"EPUB file too large: {file_size} bytes (max 50MB)")
                return False
            
            # Send email
            logger.info(f"Connecting to {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Successfully sent to {kindle_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
