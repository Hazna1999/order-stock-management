from django.contrib.auth.models import Group, User
from rest_framework import serializers

from .permissions import ALL_ROLES


class UserSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=ALL_ROLES, write_only=True)
    roles = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = User
        fields = ["id", "username", "password", "role", "roles", "is_active"]
        read_only_fields = ["id"]

    def get_roles(self, user):
        return sorted(g.name for g in user.groups.all())

    def validate(self, attrs):
        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Password is required."})
        request = self.context["request"]
        if self.instance and self.instance.pk == request.user.pk:
            if attrs.get("is_active") is False or ("role" in attrs and attrs["role"] != "Admin"):
                raise serializers.ValidationError("You cannot deactivate or demote yourself.")
        return attrs

    def _set_role(self, user, role):
        user.groups.set([Group.objects.get_or_create(name=role)[0]])

    def create(self, data):
        role = data.pop("role")
        password = data.pop("password")
        user = User(**data)
        user.set_password(password)
        user.save()
        self._set_role(user, role)
        return user

    def update(self, user, data):
        role = data.pop("role", None)
        password = data.pop("password", None)
        for k, v in data.items():
            setattr(user, k, v)
        if password:
            user.set_password(password)
        user.save()
        if role:
            self._set_role(user, role)
        return user