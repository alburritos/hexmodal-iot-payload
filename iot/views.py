"""
API views for IoT payload ingestion.

This is the entry point for POST requests from IoT devices/gateways.
"""

from django.db import IntegrityError, transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import IncomingPayloadSerializer, PayloadResponseSerializer


class PayloadCreateView(APIView):
    """
    Accept and process a single IoT payload.

    Authentication:
        Requires a DRF token in the request header:
        Authorization: Token <your-token>

        Tokens are created via: python manage.py drf_create_token <username>
    """

    # Only authenticated requests (valid token) are allowed through.
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Step 1: Validate the incoming JSON against our expected schema.
        serializer = IncomingPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Step 2: Save the payload inside an atomic block.
        # If a duplicate fCnt triggers an IntegrityError, the savepoint rolls
        # back cleanly so the rest of the request can still return a 409.
        try:
            with transaction.atomic():
                payload = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "Duplicate message: fCnt already exists for this device."},
                status=status.HTTP_409_CONFLICT,
            )

        # Step 3: Return the saved payload as JSON.
        return Response(
            PayloadResponseSerializer(payload).data,
            status=status.HTTP_201_CREATED,
        )
