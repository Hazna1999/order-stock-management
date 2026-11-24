from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import mixins, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsAdmin, user_roles
from .serializers import UserSerializer


class MeView(APIView):
    @extend_schema(responses=inline_serializer("Me", {
        "id": serializers.IntegerField(),
        "username": serializers.CharField(),
        "roles": serializers.ListField(child=serializers.CharField()),
    }))
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