# account/models.py
from decimal import Decimal

from django.db.models import CharField, DecimalField
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """自定义用户模型"""

    # 头像图片路径
    profile_image_path: CharField = CharField(
        verbose_name="头像图片路径",
        max_length=256,
        default="",
        blank=True,
    )
    # 余额
    balance: DecimalField = DecimalField(
        verbose_name="余额",
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    # API Key
    api_key: CharField = CharField(
        verbose_name="API Key",
        max_length=64,
        default="",
        blank=True,
    )

    # 移除继承的字段和方法
    first_name = None
    last_name = None

    def get_full_name(self) -> str:
        return self.username

    def get_short_name(self) -> str:
        return self.username

    class Meta:
        verbose_name: str = "账户"
        verbose_name_plural: str = "账户"
