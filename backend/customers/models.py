# Create your models here.
from django.db import models
from django.db.models.functions import Lower


class Customer(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    billing_address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="uniq_customer_email_ci"),
        ]

    def __str__(self):
        return self.name