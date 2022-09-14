from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.indexes import GinIndex
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F

from core.models import BaseModel, Cve, Product, Vendor


def get_default_settings():
    return {"activities_view": "all"}


class User(BaseModel, AbstractUser):
    settings = models.JSONField(default=get_default_settings)

    vendors = models.ManyToManyField(Vendor)
    products = models.ManyToManyField(Product)

    class Meta:
        db_table = "opencve_users"

    def __str__(self):
        return self.username

    def get_raw_vendors(self):
        vendors = list(
            User.objects.filter(id=self.id)
            .select_related("vendors")
            .values(
                vendor_id=F("vendors__id"),
                vendor_name=F("vendors__name"),
            )
        )

        if len(vendors) == 1 and set(vendors[0].values()) == {None}:
            return []

        return vendors

    def get_raw_products(self):
        products = list(
            User.objects.filter(id=self.id)
            .select_related("products")
            .select_related("vendors")
            .values(
                vendor_id=F("products__vendor__id"),
                vendor_name=F("products__vendor__name"),
                product_id=F("products__id"),
                product_name=F("products__name"),
            )
        )
        if len(products) == 1 and set(products[0].values()) == {None}:
            return []

        return products


class UserTag(BaseModel):
    name = models.CharField(
        max_length=64,
        validators=[
            RegexValidator(
                regex="^[a-zA-Z0-9\-_]+$",
                message="Only alphanumeric, dash and underscore characters are accepted",
            ),
        ],
    )
    color = models.CharField(
        max_length=7,
        validators=[
            RegexValidator(
                regex="^#[0-9a-fA-F]{6}$",
                message="Color must be in hexadecimal format",
            ),
        ],
        default="#000000",
    )
    description = models.CharField(max_length=512, null=True, blank=True)

    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags")

    class Meta:
        db_table = "opencve_users_tags"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "user_id"], name="ix_unique_name_userid"
            )
        ]

    def __str__(self):
        return self.name


class CveTag(BaseModel):
    tags = models.JSONField()

    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cve_tags")
    cve = models.ForeignKey(Cve, on_delete=models.CASCADE, related_name="cve_tags")

    class Meta:
        db_table = "opencve_cves_tags"
        indexes = [
            GinIndex(name="ix_cves_tags", fields=["tags"]),
        ]