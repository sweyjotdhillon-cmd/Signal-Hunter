"""
Telegram Delivery Transport for Signal Hunter.
Handles secure, rate-limit aware, chunk-split markdown message publication.
"""

import logging
import os
import time
from typing import List
import requests
from utils.logger import setup_logger


class TelegramSender:
    """
    Robust Telegram Delivery Service with message splitting, rate limiting, and retries.
    """

    def __init__(self, token: str = None, chat_id: str = None) -> None:
        self.logger: logging.Logger = setup_logger(
            name="signal_hunter.delivery.telegram",
            log_level="INFO",
        )
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

        if not self.token or not self.chat_id:
            self.logger.warning(
                "Telegram Bot Token or Chat ID not configured. Telegram delivery will be disabled."
            )

    def send_report(self, report_markdown: str) -> bool:
        """
        Sends the markdown report to the configured Telegram channel/chat.
        Splits long messages, respects rate limits, and uses retry logic with backoff.
        """
        if not self.token or not self.chat_id:
            self.logger.warning("Skipping Telegram delivery: Missing configuration credentials.")
            return False

        self.logger.info("Starting Telegram report delivery...")
        chunks = self._split_message(report_markdown)

        success = True
        for i, chunk in enumerate(chunks, 1):
            self.logger.info("Sending Telegram message chunk %d/%d...", i, len(chunks))
            chunk_success = self._send_chunk_with_retry(chunk)
            if not chunk_success:
                success = False
                self.logger.error("Failed to send chunk %d/%d", i, len(chunks))
            # Avoid hitting rate limits between chunks
            time.sleep(1)

        return success

    def _split_message(self, text: str, max_length: int = 4000) -> List[str]:
        """
        Splits text into chunks of at most max_length characters, trying not to split lines.
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        lines = text.split("\n")
        current_chunk = []
        current_length = 0

        for line in lines:
            line_len = len(line) + 1  # Add 1 for newline
            if current_length + line_len > max_length:
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = [line]
                    current_length = line_len
                else:
                    # Handle extremely long lines by hard splitting
                    for i in range(0, len(line), max_length):
                        chunks.append(line[i : i + max_length])
                    current_length = 0
            else:
                current_chunk.append(line)
                current_length += line_len

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _send_chunk_with_retry(self, text: str, max_retries: int = 3) -> bool:
        """
        Sends a single chunk of text with retries and exponential backoff, handling rate limits.
        """
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        delay = 2.0
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(url, json=payload, timeout=10)

                # Check for rate limiting (HTTP 429)
                if response.status_code == 429:
                    retry_after = (
                        response.json().get("parameters", {}).get("retry_after", 10)
                    )
                    self.logger.warning(
                        "Telegram API Rate Limited (429). Retrying after %d seconds. Attempt %d/%d",
                        retry_after,
                        attempt,
                        max_retries,
                    )
                    time.sleep(retry_after)
                    continue

                # Check for bad markdown or other bad requests
                if response.status_code == 400:
                    self.logger.warning(
                        "Telegram Markdown validation failed. Retrying in plain text..."
                    )
                    plain_payload = payload.copy()
                    plain_payload.pop("parse_mode", None)
                    response = requests.post(url, json=plain_payload, timeout=10)

                if response.status_code == 200:
                    self.logger.info("Telegram chunk delivered successfully.")
                    return True
                else:
                    self.logger.error(
                        "Telegram API responded with error status %d: %s",
                        response.status_code,
                        response.text,
                    )

            except requests.RequestException as e:
                self.logger.warning(
                    "Network error during Telegram delivery on attempt %d: %s",
                    attempt,
                    e,
                )

            if attempt < max_retries:
                self.logger.info("Retrying in %.1f seconds...", delay)
                time.sleep(delay)
                delay *= 2

        self.logger.error("All Telegram delivery attempts failed.")
        return False
