from django.urls import re_path

from .views import PingView

app_name = "coveredon_test.api"

urlpatterns = [
    re_path(r"ping/$", PingView.as_view(), name="ping"),
]
