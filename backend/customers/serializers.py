from rest_framework import serializers

from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=200)

    class Meta:
        model = Customer
        fields = ["id", "name", "email", "phone", "billing_address", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_name(self, value):
        return value.strip()

    def validate_email(self, value):
        value = value.strip()
        qs = Customer.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A customer with this email already exists.")
        return value