from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import IncomingPayloadSerializer, PayloadResponseSerializer


class PayloadCreateView(APIView):
    """
    Accept POST requests from IoT devices.

    Requires a valid DRF token in the Authorization header:
    Authorization: Token <your-token>
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = IncomingPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                payload = serializer.save()
        except IntegrityError:
            # Raised when fCnt was already recorded for this device.
            return Response(
                {"detail": "Duplicate message: fCnt already exists for this device."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            PayloadResponseSerializer(payload).data,
            status=status.HTTP_201_CREATED,
        )
