"""
Email integration client (SMTP / SendGrid)
"""

import logging
from typing import Dict, Any, Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EmailClient:
    """Client for sending emails via SMTP or SendGrid"""

    def __init__(self, config: Config):
        """
        Initialize email client

        Args:
            config: Application configuration
        """
        self.config = config
        self.provider = config.integrations.email.provider

    async def send_meeting_summary(
        self,
        recipients: List[str],
        subject: str,
        summary_html: str,
        summary_text: str = None,
        attachments: List[str] = None
    ) -> bool:
        """
        Send meeting summary email

        Args:
            recipients: List of recipient email addresses
            subject: Email subject
            summary_html: HTML content of the summary
            summary_text: Plain text version (optional)
            attachments: List of file paths to attach

        Returns:
            True if successful
        """
        if not self.config.integrations.email.enabled:
            logger.info("Email integration disabled")
            return False

        try:
            if self.provider == "smtp":
                return await self._send_smtp(
                    recipients, subject, summary_html, summary_text, attachments
                )
            elif self.provider == "sendgrid":
                return await self._send_sendgrid(
                    recipients, subject, summary_html, summary_text, attachments
                )
            else:
                logger.error(f"Unsupported email provider: {self.provider}")
                return False

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    async def _send_smtp(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: str = None,
        attachments: List[str] = None
    ) -> bool:
        """Send email via SMTP"""
        try:
            import smtplib
            from email.mime.base import MIMEBase
            from email import encoders

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.integrations.email.sender_email
            msg['To'] = ', '.join(recipients)

            # Add text content
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename="{attachment_path.split("/")[-1]}"'
                        )
                        msg.attach(part)

            # Send email
            server = smtplib.SMTP(
                self.config.integrations.email.smtp_server,
                self.config.integrations.email.smtp_port
            )

            if self.config.integrations.email.use_tls:
                server.starttls()

            if self.config.integrations.email.sender_password:
                server.login(
                    self.config.integrations.email.sender_email,
                    self.config.integrations.email.sender_password.get_secret_value()
                )

            server.sendmail(
                self.config.integrations.email.sender_email,
                recipients,
                msg.as_string()
            )

            server.quit()

            logger.info(f"Email sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            logger.error(f"SMTP send failed: {str(e)}")
            return False

    async def _send_sendgrid(
        self,
        recipients: List[str],
        subject: str,
        html_content: str,
        text_content: str = None,
        attachments: List[str] = None
    ) -> bool:
        """Send email via SendGrid"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

            # This would require SendGrid API key
            # Implementation would go here

            logger.warning("SendGrid implementation not yet complete")
            return False

        except ImportError:
            logger.error("SendGrid dependencies not installed")
            return False
        except Exception as e:
            logger.error(f"SendGrid send failed: {str(e)}")
            return False

    def generate_summary_html(self, meeting_data: Dict[str, Any]) -> str:
        """
        Generate HTML email content from meeting data

        Args:
            meeting_data: Meeting data dictionary

        Returns:
            HTML email content
        """
        summary = meeting_data.get('summary', {})
        tasks = meeting_data.get('tasks', [])

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #f0f0f0; padding: 10px; }}
                .section {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{summary.get('title', 'Meeting Summary')}</h1>
                <p><strong>Date:</strong> {summary.get('date', 'N/A')}</p>
                <p><strong>Meeting ID:</strong> {summary.get('meeting_id', 'N/A')}</p>
            </div>

            <div class="section">
                <h2>Participants</h2>
                <ul>
        """

        for participant in summary.get('participants', []):
            html += f"<li>{participant}</li>"

        html += """
                </ul>
            </div>

            <div class="section">
                <h2>Summary</h2>
                <p>""" + summary.get('summary', 'No summary available') + """</p>
            </div>

            <div class="section">
                <h2>Action Items</h2>
                <table>
                    <tr>
                        <th>Task</th>
                        <th>Assignee</th>
                        <th>Due Date</th>
                        <th>Priority</th>
                    </tr>
        """

        for task in tasks:
            html += f"""
                    <tr>
                        <td>{task.get('title', '')}</td>
                        <td>{task.get('assignee', '')}</td>
                        <td>{task.get('due_date', 'N/A')}</td>
                        <td>{task.get('priority', 'Medium')}</td>
                    </tr>
            """

        html += """
                </table>
            </div>
        </body>
        </html>
        """

        return html