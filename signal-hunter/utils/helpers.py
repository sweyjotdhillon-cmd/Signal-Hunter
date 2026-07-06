"""
Signal Hunter General Utility Helpers.

Common functional routines for filesystem operations, string sanitization,
and cryptographic hashing for ID consistency.
"""

import hashlib
import json
import os
import re
from typing import Any, Dict, Optional


def generate_id(url: str) -> str:
    """
    Generate a deterministic SHA-256 identifier based on a canonical URL.

    Args:
        url (str): Canonical source URL.

    Returns:
        str: 64-character hexadecimal SHA-256 hash.
    """
    cleaned_url = url.strip().lower()
    return hashlib.sha256(cleaned_url.encode("utf-8")).hexdigest()


def safe_write_json(filepath: str, data: Any, indent: int = 4) -> None:
    """
    Safely write data structure to a JSON file, creating parent directories if missing.

    Args:
        filepath (str): Absolute or relative filesystem destination path.
        data (Any): JSON-serializable dictionary or list.
        indent (int): Visual spacing indentation size.
    """
    dir_path = os.path.dirname(filepath)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    # Write to a temporary file first, then rename (atomic write)
    temp_filepath = f"{filepath}.tmp"
    try:
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        os.replace(temp_filepath, filepath)
    except Exception as e:
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
        raise OSError(f"Failed to write JSON securely to {filepath}: {e}") from e


def safe_read_json(filepath: str) -> Optional[Any]:
    """
    Safely load data structure from a JSON file. Returns None if the file is absent.

    Args:
        filepath (str): Filesystem path to read from.

    Returns:
        Optional[Any]: Loaded Python structure or None if not found/invalid.
    """
    if not os.path.exists(filepath):
        return None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Gracefully handle corrupted files or locked reads
        return None


def sanitize_text(text: str) -> str:
    """
    Sanitize and clean raw text by collapsing consecutive whitespaces.

    Args:
        text (str): Raw string.

    Returns:
        str: Trimmed, formatted string.
    """
    if not text:
        return ""
    # Collapse multiple spaces and newlines into single spaces/newlines
    cleaned = re.sub(r"\s+", " ", text)
    return cleaned.strip()
