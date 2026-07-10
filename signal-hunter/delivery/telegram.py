"""
Signal Hunter - Outbound Telegram Delivery Publisher.
Handles transmission of compiled intelligence briefings to configured Telegram channels.
"""

import os
import logging
import requests

logger = logging.getLogger("signal_hunter.delivery.telegram")


class TelegramSender:
    """
    Adapter for broadcasting markdown intelligence documents to a Telegram channel/chat.
    """

    def __init__(self) -> None:
        # Load credentials from standard environment variables
        self.token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

    def send_report(self, message: str) -> bool:
        """
        Transmits a text message or markdown report to the configured Telegram chat.
        """
        if not self.token or not self.chat_id:
            logger.warning("Telegram token or chat_id is missing. Skipping transmission.")
            return False

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        # Telegram sendMessage parameters
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            logger.info("Transmitting briefing to Telegram chat %s...", self.chat_id)
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                logger.info("Telegram notification successfully delivered!")
                return True
            else:
                logger.error(
                    "Telegram transmission rejected with status code %d: %s",
                    response.status_code,
                    response.text,
                )
                return False
        except Exception as e:
            logger.error("Failed to connect to Telegram API: %s", e)
            return False
