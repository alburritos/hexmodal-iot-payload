from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from iot.models import Device, Payload

SAMPLE_PAYLOAD = {
    "fCnt": 100,
    "devEUI": "abcdabcdabcdabcd",
    "data": "AQ==",
    "rxInfo": [
        {
            "gatewayID": "1234123412341234",
            "name": "G1",
            "time": "2022-07-19T11:00:00",
            "rssi": -57,
            "loRaSNR": 10,
        }
    ],
    "txInfo": {"frequency": 86810000, "dr": 5},
}


class PayloadCreateViewTests(APITestCase):
    def setUp(self):
        self.url = reverse("payload-create")
        self.user = User.objects.create_user(username="iot_device", password="secret")
        self.token = Token.objects.create(user=self.user)
        self.auth_header = {"HTTP_AUTHORIZATION": f"Token {self.token.key}"}

    def test_requires_authentication(self):
        response = self.client.post(self.url, SAMPLE_PAYLOAD, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_creates_passing_payload(self):
        response = self.client.post(
            self.url, SAMPLE_PAYLOAD, format="json", **self.auth_header
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data_hex"], "01")
        self.assertEqual(response.data["status"], Payload.Status.PASSING)

        device = Device.objects.get(dev_eui=SAMPLE_PAYLOAD["devEUI"])
        self.assertEqual(device.latest_status, Payload.Status.PASSING)
        self.assertEqual(device.payloads.count(), 1)

        payload = Payload.objects.get(f_cnt=100)
        self.assertEqual(payload.rx_info, SAMPLE_PAYLOAD["rxInfo"])
        self.assertEqual(payload.tx_info, SAMPLE_PAYLOAD["txInfo"])

    def test_creates_failing_payload(self):
        payload_data = {**SAMPLE_PAYLOAD, "fCnt": 101, "data": "Ag=="}

        response = self.client.post(
            self.url, payload_data, format="json", **self.auth_header
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data_hex"], "02")
        self.assertEqual(response.data["status"], Payload.Status.FAILING)

        device = Device.objects.get(dev_eui=SAMPLE_PAYLOAD["devEUI"])
        self.assertEqual(device.latest_status, Payload.Status.FAILING)

    def test_rejects_duplicate_fcnt(self):
        self.client.post(self.url, SAMPLE_PAYLOAD, format="json", **self.auth_header)

        response = self.client.post(
            self.url, SAMPLE_PAYLOAD, format="json", **self.auth_header
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Payload.objects.filter(f_cnt=100).count(), 1)

    def test_rejects_invalid_base64(self):
        invalid_payload = {**SAMPLE_PAYLOAD, "data": "not-valid-base64!"}

        response = self.client.post(
            self.url, invalid_payload, format="json", **self.auth_header
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
