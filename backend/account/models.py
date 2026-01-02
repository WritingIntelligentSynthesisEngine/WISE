# account/models.py
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    # 余额
    balance = models.DecimalField(
        verbose_name="余额",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    # API Key
    api_key = models.CharField(
        verbose_name="API Key",
        max_length=64,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name: str = "账户"
        verbose_name_plural: str = "账户"
