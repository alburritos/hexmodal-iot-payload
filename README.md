# Hexmodal IoT Payload Parser

A small Django REST Framework application that receives IoT device payloads, authenticates requests via token, deduplicates messages by `fCnt`, decodes Base64 data to hexadecimal, and tracks pass/fail status per device.

## Requirements

- Python 3.10+

## Setup

```bash
# Clone the repository and enter the project directory
git clone <your-repo-url>
cd hex_7-22-26

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
