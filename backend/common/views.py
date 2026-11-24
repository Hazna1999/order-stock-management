from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import user_roles


class MeView(APIView):
    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "roles": sorted(user_roles(request.user)),
        })