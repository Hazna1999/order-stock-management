from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import user_roles
from django.contrib.auth.models import User
from rest_framework import mixins, viewsets

from .permissions import IsAdmin
from .serializers import UserSerializer



class MeView(APIView):
    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "roles": sorted(user_roles(request.user)),
        })

class UserViewSet(
    mixins.CreateModelMixin, mixins.ListModelMixin,
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet,
):
    queryset = User.objects.prefetch_related("groups").order_by("username")
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    search_fields = ["username"]