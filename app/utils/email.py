"""
Email utility functions for sending notifications.
"""
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class EmailService:
    """Email service for sending various types of emails."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.use_tls = settings.SMTP_USE_TLS
    
    def _create_smtp_connection(self) -> smtplib.SMTP:
        """Create and configure SMTP connection."""
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
            
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)
            
            return server
            
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        cc_emails: Optional[List[str]] = None,
        bcc_emails: Optional[List[str]] = None,
        attachments: Optional[List[Path]] = None
    ) -> bool:
        """
        Send email with optional attachments.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML content of the email
            text_content: Plain text content (optional)
            cc_emails: List of CC email addresses
            bcc_emails: List of BCC email addresses
            attachments: List of file paths to attach
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MimeMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
            
            # Add text content
            if text_content:
                text_part = MimeText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML content
            html_part = MimeText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachments
            if attachments:
                for file_path in attachments:
                    if file_path.exists():
                        with open(file_path, 'rb') as attachment:
                            part = MimeBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {file_path.name}'
                            )
                            msg.attach(part)
            
            # Send email
            with self._create_smtp_connection() as server:
                all_recipients = to_emails[:]
                if cc_emails:
                    all_recipients.extend(cc_emails)
                if bcc_emails:
                    all_recipients.extend(bcc_emails)
                
                server.send_message(msg, to_addrs=all_recipients)
            
            logger.info(f"Email sent successfully to {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Email templates
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to Hotel Booking System',
        'html': '''
        <html>
        <body>
            <h2>Welcome to Hotel Booking System!</h2>
            <p>Hi {first_name},</p>
            <p>Thank you for registering with our hotel booking system. Your account has been created successfully.</p>
            <p>You can now start booking hotels and managing your reservations.</p>
            <p>If you have any questions, please don't hesitate to contact our support team.</p>
            <br>
            <p>Best regards,<br>Hotel Booking Team</p>
        </body>
        </html>
        '''
    },
    
    'email_verification': {
        'subject': 'Verify Your Email Address',
        'html': '''
        <html>
        <body>
            <h2>Email Verification Required</h2>
            <p>Hi {first_name},</p>
            <p>Please verify your email address by clicking the link below:</p>
            <p><a href="{verification_link}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>If you didn't create this account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Hotel Booking Team</p>
        </body>
        </html>
        '''
    },
    
    'password_reset': {
        'subject': 'Reset Your Password',
        'html': '''
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hi {first_name},</p>
            <p>You requested to reset your password. Click the link below to create a new password:</p>
            <p><a href="{reset_link}" style="background-color: #ff6b6b; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this, please ignore this email and your password will remain unchanged.</p>
            <br>
            <p>Best regards,<br>Hotel Booking Team</p>
        </body>
        </html>
        '''
    },
    
    'booking_confirmation': {
        'subject': 'Booking Confirmation - {hotel_name}',
        'html': '''
        <html>
        <body>
            <h2>Booking Confirmation</h2>
            <p>Hi {guest_name},</p>
            <p>Your booking has been confirmed! Here are the details:</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px;">
                <h3>Booking Details</h3>
                <p><strong>Booking Reference:</strong> {booking_reference}</p>
                <p><strong>Hotel:</strong> {hotel_name}</p>
                <p><strong>Room Type:</strong> {room_type}</p>
                <p><strong>Check-in:</strong> {check_in_date}</p>
                <p><strong>Check-out:</strong> {check_out_date}</p>
                <p><strong>Guests:</strong> {guest_count}</p>
                <p><strong>Total Amount:</strong> ${total_amount}</p>
            </div>
            
            <p>We look forward to welcoming you to {hotel_name}!</p>
            <p>If you need to modify or cancel your booking, please contact us at least 24 hours before your check-in date.</p>
            <br>
            <p>Best regards,<br>Hotel Booking Team</p>
        </body>
        </html>
        '''
    },
    
    'booking_cancellation': {
        'subject': 'Booking Cancellation - {hotel_name}',
        'html': '''
        <html>
        <body>
            <h2>Booking Cancellation</h2>
            <p>Hi {guest_name},</p>
            <p>Your booking has been cancelled as requested. Here are the details:</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px;">
                <h3>Cancelled Booking Details</h3>
                <p><strong>Booking Reference:</strong> {booking_reference}</p>
                <p><strong>Hotel:</strong> {hotel_name}</p>
                <p><strong>Original Check-in:</strong> {check_in_date}</p>
                <p><strong>Original Check-out:</strong> {check_out_date}</p>
                <p><strong>Refund Amount:</strong> ${refund_amount}</p>
            </div>
            
            <p>The refund will be processed within 3-5 business days and will appear on your original payment method.</p>
            <p>Thank you for using our booking system. We hope to serve you again in the future.</p>
            <br>
            <p>Best regards,<br>Hotel Booking Team</p>
        </body>
        </html>
        '''
    },
    
    'payment_receipt': {
        'subject': 'Payment Receipt - {hotel_name}',
        'html': '''
        <html>
        <body>
            <h2>Payment Receipt</h2>
            <p>Hi {guest_name},</p>
            <p>Thank you for your payment. Here is your receipt:</p>
            
            <div style="background-color: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px;">
                <h3>Payment Details</h3>
                <p><strong>Transaction ID:</strong> {transaction_id}</p>
                <p><strong>Booking Reference:</strong> {booking_reference}</p>
                <p><strong>Hotel:</strong> {hotel_name}</p>
                <p><strong>Payment Date:</strong> {payment_date}</p>
                <p><strong>Amount Paid:</strong> ${amount_paid}</p>
                <p><strong>Payment Method:</strong> {payment_method}</p>
            </div>
            
            <p>This receipt serves as proof of payment for your booking.</p>
            <p>If you have any questions about this payment, please contact our support team.</p>
            <br>
            <p>Best regards,<br>Hotel Booking Team</p>
        </body>
        </html>
        '''
    }
}


def send_templated_email(
    template_name: str,
    to_emails: List[str],
    template_data: Dict[str, Any],
    email_service: Optional[EmailService] = None
) -> bool:
    """
    Send email using predefined template.
    
    Args:
        template_name: Name of the email template
        to_emails: List of recipient email addresses
        template_data: Data to populate template placeholders
        email_service: Email service instance (optional)
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if template_name not in EMAIL_TEMPLATES:
        logger.error(f"Unknown email template: {template_name}")
        return False
    
    template = EMAIL_TEMPLATES[template_name]
    
    try:
        # Format subject and content with template data
        subject = template['subject'].format(**template_data)
        html_content = template['html'].format(**template_data)
        
        # Create email service if not provided
        if email_service is None:
            email_service = EmailService()
        
        # Send email
        return email_service.send_email(
            to_emails=to_emails,
            subject=subject,
            html_content=html_content
        )
        
    except KeyError as e:
        logger.error(f"Missing template data key: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send templated email: {e}")
        return False


def send_welcome_email(user_email: str, first_name: str) -> bool:
    """Send welcome email to new user."""
    return send_templated_email(
        template_name='welcome',
        to_emails=[user_email],
        template_data={'first_name': first_name}
    )


def send_verification_email(user_email: str, first_name: str, verification_link: str) -> bool:
    """Send email verification email."""
    return send_templated_email(
        template_name='email_verification',
        to_emails=[user_email],
        template_data={
            'first_name': first_name,
            'verification_link': verification_link
        }
    )


def send_password_reset_email(user_email: str, first_name: str, reset_link: str) -> bool:
    """Send password reset email."""
    return send_templated_email(
        template_name='password_reset',
        to_emails=[user_email],
        template_data={
            'first_name': first_name,
            'reset_link': reset_link
        }
    )


def send_booking_confirmation_email(
    user_email: str,
    booking_data: Dict[str, Any]
) -> bool:
    """Send booking confirmation email."""
    return send_templated_email(
        template_name='booking_confirmation',
        to_emails=[user_email],
        template_data=booking_data
    )
