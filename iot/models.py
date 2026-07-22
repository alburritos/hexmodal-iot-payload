from django.db import models


class Device(models.Model):
    """IoT device identified by its devEUI."""

    class Status(models.TextChoices):
        PASSING = "passing", "Passing"
        FAILING = "failing", "Failing"

    dev_eui = models.CharField(max_length=16, unique=True)
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
    """Incoming message from an IoT device."""

    class Status(models.TextChoices):
        PASSING = "passing", "Passing"
        FAILING = "failing", "Failing"

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name="payloads",
    )
    f_cnt = models.IntegerField()
    data = models.TextField()
    data_hex = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices)
    rx_info = models.JSONField(default=list)
    tx_info = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # fCnt is a monotonic counter per device; duplicates must be rejected.
        constraints = [
            models.UniqueConstraint(
                fields=["device", "f_cnt"],
                name="unique_device_fcnt",
            )
        ]

    def __str__(self):
        return f"{self.device.dev_eui} fCnt={self.f_cnt}"
