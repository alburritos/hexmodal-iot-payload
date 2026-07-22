from django.urls import path

from .views import PayloadCreateView

urlpatterns = [
    path("payloads/", PayloadCreateView.as_view(), name="payload-create"),
]
