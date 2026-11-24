from rest_framework import mixins, viewsets

from common.permissions import IsAdminOrSales

from .models import Customer
from .serializers import CustomerSerializer


class CustomerViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminOrSales]
    filterset_fields = ["is_active"]
    search_fields = ["name", "email"]