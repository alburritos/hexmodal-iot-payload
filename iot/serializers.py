from rest_framework import serializers

from .models import Payload
from .services import decode_payload_data, evaluate_payload_status


class IncomingPayloadSerializer(serializers.Serializer):
    """Validates the JSON body sent by IoT devices."""

    fCnt = serializers.IntegerField()
    devEUI = serializers.CharField(max_length=16)
    data = serializers.CharField()
    rxInfo = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    txInfo = serializers.DictField(required=False, default=dict)

    def validate_data(self, value):
        try:
            decode_payload_data(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc
        return value

    def create(self, validated_data):
        from .models import Device

        hex_value, int_value = decode_payload_data(validated_data["data"])
        status = evaluate_payload_status(int_value)

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

        # Keep the device's latest status in sync with its most recent payload.
        device.latest_status = status
        device.save(update_fields=["latest_status", "updated_at"])

        return payload


class PayloadResponseSerializer(serializers.ModelSerializer):
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
