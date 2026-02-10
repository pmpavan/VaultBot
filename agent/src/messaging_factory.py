from agent.src.infrastructure.twilio_adapter import TwilioMessagingService
from agent.src.interfaces.messaging import MessagingProvider

def get_messaging_provider() -> MessagingProvider:
    """
    Factory to return the configured messaging provider.
    In the future, this could choose between different providers based on config.
    """
    return TwilioMessagingService()
