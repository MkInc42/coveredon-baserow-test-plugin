from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny


class PingView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response(
            {
                "plugin": "coveredon_test",
                "status": "ok",
                "baserow_version": "2.3.3",
            }
        )
