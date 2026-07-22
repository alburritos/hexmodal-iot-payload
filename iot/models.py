"""
Database models for IoT device ingestion.

This app receives uplink messages from LoRaWAN-style IoT devices (via a gateway
or integration). Each message is stored as a Payload and linked to a Device.
"""

from django.db import models


class Device(models.Model):
    """
    Represents a physical IoT device.

    Devices are identified by devEUI, a unique 16-character identifier assigned
    to each LoRaWAN device. We store one row per device and update
    `latest_status` whenever a new payload is accepted.
    """

    class Status(models.TextChoices):
        PASSING = "passing", "Passing"
        FAILING = "failing", "Failing"

    # LoRaWAN device identifier; maps to the "devEUI" field in incoming JSON.
    dev_eui = models.CharField(max_length=16, unique=True)

    # Most recent pass/fail result from the device's latest accepted payload.
    # Null until the device sends its first message.
    latest_status = models.CharField(
        max_length=10,
        choices=Status.choices,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dev_eui


class Payload(models.Model):
    """
    A single incoming message from an IoT device.

    The raw JSON uses camelCase keys (fCnt, devEUI, rxInfo) as sent by the
    device/gateway. We normalize those to snake_case when saving to the database.
    """

    class Status(models.TextChoices):
        PASSING = "passing", "Passing"
        FAILING = "failing", "Failing"

    # Links this payload to the device that sent it (matched by devEUI).
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="payloads",
    )

    # Frame counter (fCnt): increments with each transmission from the device.
    # Used to detect duplicate/replayed messages — see Meta.constraints below.
    f_cnt = models.IntegerField()

    # Original base64-encoded sensor data as received from the device.
    data = models.TextField()

    # Human-readable hex representation of `data` after base64 decoding.
    # Example: "AQ==" decodes to the byte 0x01, stored here as "01".
    data_hex = models.CharField(max_length=255)

    # Pass/fail result derived from the decoded data value (1 = passing).
    status = models.CharField(max_length=10, choices=Status.choices)

    # Radio/gateway metadata from the incoming JSON (optional fields).
    rx_info = models.JSONField(default=list)  # Receive info: RSSI, SNR, gateway ID, etc.
    tx_info = models.JSONField(default=dict)  # Transmit info: frequency, data rate, etc.

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Enforce at the database level: the same (device, fCnt) pair cannot
        # be stored twice. This is our primary duplicate-message guard.
        constraints = [
            models.UniqueConstraint(
                fields=["device", "f_cnt"],
                name="unique_device_fcnt",
            )
        ]

    def __str__(self):
        return f"{self.device.dev_eui} fCnt={self.f_cnt}"
