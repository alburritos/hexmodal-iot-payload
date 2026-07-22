"""
DRF serializers for validating incoming IoT payloads and formatting responses.

Request flow for a POST /api/payloads/:
  1. IncomingPayloadSerializer validates the JSON body
  2. create() decodes data, evaluates pass/fail, saves Payload + updates Device
  3. PayloadResponseSerializer shapes the JSON sent back to the caller
"""

from rest_framework import serializers

from .models import Payload
from .services import decode_payload_data, evaluate_payload_status


class IncomingPayloadSerializer(serializers.Serializer):
    """
    Validates the JSON body sent by IoT devices or gateways.

    Field names intentionally match the incoming JSON (camelCase) so DRF can
    map them directly from the request body without extra configuration.
    """

    fCnt = serializers.IntegerField()
    devEUI = serializers.CharField(max_length=16)
    data = serializers.CharField()
    rxInfo = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    txInfo = serializers.DictField(required=False, default=dict)

    def validate_data(self, value):
        """
        Reject invalid base64 early, before we attempt to save anything.

        DRF calls validate_<field_name>() automatically during is_valid().
        """
        try:
            decode_payload_data(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def create(self, validated_data):
        """
        Persist a new Payload and update the parent Device.

        Called by serializer.save() after validation passes. This is where the
        main business logic runs: decode -> evaluate -> save.
        """
        from .models import Device

        hex_value, int_value = decode_payload_data(validated_data["data"])
        status = evaluate_payload_status(int_value)

        # First message from a device auto-creates the Device record.
        device, _ = Device.objects.get_or_create(dev_eui=validated_data["devEUI"])

        payload = Payload.objects.create(
            device=device,
            f_cnt=validated_data["fCnt"],
            data=validated_data["data"],
            data_hex=hex_value,
            status=status,
            rx_info=validated_data.get("rxInfo", []),
            tx_info=validated_data.get("txInfo", {}),
        )

        # Denormalized field: lets us check a device's current state without
        # querying the full payload history.
        device.latest_status = status
        device.save(update_fields=["latest_status", "updated_at"])

        return payload


class PayloadResponseSerializer(serializers.ModelSerializer):
    """
    Formats a saved Payload for the API response.

    Uses snake_case field names (Django convention) in the response body.
    """

    class Meta:
        model = Payload
        fields = [
            "id",
            "f_cnt",
            "data",
            "data_hex",
            "status",
            "rx_info",
            "tx_info",
            "created_at",
        ]
