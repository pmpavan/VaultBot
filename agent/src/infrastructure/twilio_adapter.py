import os
import logging
from twilio.rest import Client
from ..interfaces.messaging import MessagingProvider
from typing import Optional

logger = logging.getLogger(__name__)

class TwilioMessagingService(MessagingProvider):
    """
    Twilio implementation of the MessagingProvider.
    """
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None, default_from: Optional[str] = None):
        self.account_sid = account_sid or os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.environ.get('TWILIO_AUTH_TOKEN')
        self.default_from = default_from or os.environ.get('TWILIO_PHONE_NUMBER')
        
        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials not found. Messaging will be disabled.")
            self.client = None
        else:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None

    def send_message(self, to: str, body: str, from_: Optional[str] = None) -> None:
        if not self.client:
            logger.warning("Twilio client not initialized. Skipping message.")
            return

        try:
            # Ensure WhatsApp formatting if needed
            # This logic was previously repeated in every worker
            target_to = to
            if not target_to.startswith('whatsapp:'):
                target_to = f"whatsapp:{target_to}"
            
            target_from = from_ or self.default_from
            if target_from and target_to.startswith('whatsapp:') and not target_from.startswith('whatsapp:'):
                target_from = f"whatsapp:{target_from}"
                
            if not target_from:
                logger.error("No sender 'from' number specified/configured.")
                return

            self.client.messages.create(
                from_=target_from,
                to=target_to,
                body=body
            )
            logger.info(f"Message sent to {to}")
            
        except Exception as e:
            logger.error(f"Failed to send Twilio message to {to}: {e}")
            # We ideally shouldn't raise here to prevent worker crash, just log error
