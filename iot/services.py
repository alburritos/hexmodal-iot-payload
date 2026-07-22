"""
Business logic for decoding and evaluating IoT payload data.

Kept separate from models/views so the core rules are easy to test and reuse.
"""

import base64
import binascii


def decode_payload_data(data_b64: str) -> tuple[str, int]:
    """
    Decode the base64 `data` field from an IoT payload.

    IoT gateways typically send sensor readings as base64-encoded bytes.
    We convert that into:
      - a hex string (for storage/display)
      - an integer value (for pass/fail evaluation)

    Example:
        "AQ==" -> base64 decodes to byte 0x01 -> hex "01", int 1

    Returns:
        (hex_string, integer_value)

    Raises:
        ValueError: if the input is not valid base64.
    """
    try:
        raw_bytes = base64.b64decode(data_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 data.") from exc

    hex_value = raw_bytes.hex()
    # Big-endian: for single-byte payloads this is just the byte value itself.
    int_value = int.from_bytes(raw_bytes, byteorder="big") if raw_bytes else 0
    return hex_value, int_value


def evaluate_payload_status(int_value: int) -> str:
    """
    Determine pass/fail from the decoded sensor value.

    Per the challenge spec: a decoded value of 1 means passing; anything else
    is failing.
    """
    from .models import Payload

    if int_value == 1:
        return Payload.Status.PASSING
    return Payload.Status.FAILING
