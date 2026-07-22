# Hexmodal IoT Payload Parser

A small Django REST Framework application that receives IoT device payloads, authenticates requests via token, deduplicates messages by `fCnt`, decodes Base64 data to hexadecimal, and tracks pass/fail status per device.

## Requirements

- Python 3.10+

## Setup

```bash
# Clone the repository and enter the project directory
git clone https://github.com/alburritos/hexmodal-iot-payload.git
cd hexmodal-iot-payload

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
python manage.py migrate

# Create a superuser (optional, for Django admin)
python manage.py createsuperuser

# Create an API token for a user (used by IoT devices)
python manage.py drf_create_token <username>
```

## Run the server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/payloads/`.

## API Usage

### Authentication

Include a DRF token in every request:

```
Authorization: Token <your-token-here>
```

### POST /api/payloads/

Submit an IoT payload:

```bash
curl -X POST http://127.0.0.1:8000/api/payloads/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token <your-token-here>" \
  -d '{
    "fCnt": 100,
    "devEUI": "abcdabcdabcdabcd",
    "data": "AQ==",
    "rxInfo": [
      {
        "gatewayID": "1234123412341234",
        "name": "G1",
        "time": "2022-07-19T11:00:00",
        "rssi": -57,
        "loRaSNR": 10
      }
    ],
    "txInfo": {"frequency": 86810000, "dr": 5}
  }'
```

### Behavior

| Field | Description |
|-------|-------------|
| `devEUI` | Links the payload to a `Device` record (created automatically if new) |
| `fCnt` | Frame counter; duplicate `(device, fCnt)` pairs return `409 Conflict` |
| `data` | Base64-encoded bytes, decoded to hex (e.g. `AQ==` → `01`) |
| Status | Decoded value `1` → **passing**; any other value → **failing** |

Each device's `latest_status` is updated whenever a new payload is accepted.

### Example response (201 Created)

```json
{
  "id": 1,
  "f_cnt": 100,
  "data": "AQ==",
  "data_hex": "01",
  "status": "passing",
  "rx_info": [...],
  "tx_info": {...},
  "created_at": "2026-07-22T21:00:00Z"
}
```

## Project structure

```
hexmodal/          # Django project settings
iot/               # App with Device & Payload models, API endpoint
  models.py        # ORM models
  services.py      # Base64 → hex decoding and pass/fail logic
  serializers.py   # Request validation and object creation
  views.py         # Token-authenticated POST endpoint
```

## Django Admin

Visit `http://127.0.0.1:8000/admin/` to browse devices and payloads after creating a superuser.

## Glossary

This app ingests **LoRaWAN-style** uplink messages — JSON payloads sent by IoT devices through a radio gateway. The terms below appear in the incoming JSON and throughout the codebase.

| Term | Meaning |
|------|---------|
| **LoRaWAN** | A low-power, wide-area networking protocol used by many IoT sensors. Devices transmit small data packets to nearby gateways, which forward them to an application server (this app). |
| **devEUI** | **Device Extended Unique Identifier.** A 16-character hex ID that uniquely identifies a physical IoT device (e.g. `abcdabcdabcdabcd`). Used to link each payload to a `Device` record. Stored as `dev_eui` in the database (snake_case). |
| **fCnt** | **Frame Counter.** A number that increments with each transmission from a device. Used to detect duplicate or replayed messages — the same `(devEUI, fCnt)` pair is rejected with `409 Conflict`. Stored as `f_cnt` in the database. |
| **data** | The sensor reading, **Base64-encoded**. IoT devices send raw bytes; gateways often wrap them in Base64 for JSON transport. Example: `AQ==` decodes to the byte `0x01`. |
| **data_hex** | The decoded `data` field shown as a **hexadecimal string**. Example: `AQ==` → `01`. Stored on the `Payload` model for easy reading and debugging. |
| **rxInfo** | **Receive Info.** An array of objects describing how gateways received the transmission. Stored as `rx_info` in the database. Each entry can include gateway ID, signal strength, and timing. |
| **txInfo** | **Transmit Info.** An object describing how the device sent the transmission (frequency, data rate, etc.). Stored as `tx_info` in the database. |
| **gatewayID** | The unique identifier of the **LoRa gateway** that received the device's signal and forwarded the message. |
| **rssi** | **Received Signal Strength Indicator.** Measured in dBm (e.g. `-57`). Higher (less negative) values mean a stronger signal. |
| **loRaSNR** | **LoRa Signal-to-Noise Ratio.** Measured in dB (e.g. `10`). Higher values mean a cleaner signal relative to background noise. |
| **frequency** | The radio frequency (in Hz) the device used to transmit (e.g. `868100000` = 868.1 MHz, a common LoRaWAN band in Europe). |
| **dr** | **Data Rate.** An index (0–7 in LoRaWAN) indicating the transmission speed and spreading factor. Higher data rates send faster but over shorter distances. |
| **passing / failing** | The app's evaluation of a payload. If the decoded `data` value equals `1`, the payload is **passing**; any other value is **failing**. |
| **latest_status** | A field on the `Device` model tracking the most recent pass/fail result from that device's latest accepted payload. |
