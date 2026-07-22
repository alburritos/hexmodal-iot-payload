import base64
import binascii


def decode_payload_data(data_b64: str) -> tuple[str, int]:
    """
    Decode base64 payload data into a hex string and numeric value.

    Returns (hex_string, integer_value). The integer is derived from the
    decoded bytes (big-endian) and drives pass/fail evaluation.
    """
    try:
        raw_bytes = base64.b64decode(data_b64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Invalid base64 data.") from exc

    hex_value = raw_bytes.hex()
    int_value = int.from_bytes(raw_bytes, byteorder="big") if raw_bytes else 0
    return hex_value, int_value


def evaluate_payload_status(int_value: int) -> str:
    """A decoded value of 1 is passing; anything else is failing."""
    from .models import Payload

    if int_value == 1:
        return Payload.Status.PASSING
    return Payload.Status.FAILING
