"""Provider-neutral, versioned context estimation."""

from __future__ import annotations


ESTIMATOR_VERSION = "utf8_bytes_div_4_v1"


def estimate_tokens(text: str) -> int:
    """Estimate tokens with the approved ceil(UTF-8 bytes / 4) baseline."""

    if not isinstance(text, str):
        raise TypeError("Token estimation requires text input.")
    byte_count = len(text.encode("utf-8"))
    return (byte_count + 3) // 4
