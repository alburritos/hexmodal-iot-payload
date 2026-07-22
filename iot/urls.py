"""
URL routes for the iot app.

Mounted at /api/ in the project-level urls.py, so the full path is:
    POST /api/payloads/
"""

from django.urls import path

from .views import PayloadCreateView

urlpatterns = [
    path("payloads/", PayloadCreateView.as_view(), name="payload-create"),
]
