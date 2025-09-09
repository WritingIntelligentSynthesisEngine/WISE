# book/models.py
from typing import Any, Self, Literal, List, Tuple

from django.utils import timezone
from django.contrib.auth.models import User, UserManager
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Model, AutoField, IntegerField, CharField, TextField, DateTimeField, JSONField, ForeignKey, Avg, CASCADE


# Create your models here.
class Category(Model):
    """书籍分类模型, 存储书籍的分类类型"""

    # 自增主键
    id: AutoField = AutoField(
        primary_key=True,
    )
    # 分类类型
    type: CharField = CharField(
        verbose_name="分类名",
        max_length=16,
    )

    class Meta:
        verbose_name: str = "分类"
        verbose_name_plural: str = "分类"
        # 按类型升序
        ordering: List[str] = ["type"]

    def __str__(self: Self) -> str:
        return self.type


class Book(Model):
    """书籍模型, 存储书籍的基本信息"""

    # 自增主键
    id: AutoField = AutoField(
        primary_key=True,
    )
    # 分类外键
    category: ForeignKey = ForeignKey(
        Category,
        verbose_name="分类名",
        on_delete=CASCADE,
        null=True,
        blank=True,
    )
    # 书籍标题
    title: CharField = CharField(
        verbose_name="书名",
        max_length=128,
    )
    # 简介
    description: TextField = TextField(
        verbose_name="简介",
        default="无",
    )
    # 封面图片路径
    cover_image_path: CharField = CharField(
        verbose_name="封面图片路径",
        max_length=256,
        default="",
        blank=True,
    )
    # 创建时间
    create_time: DateTimeField = DateTimeField(
        verbose_name="创建时间",
        default=timezone.now,
    )
    # 更新时间
    update_time: DateTimeField = DateTimeField(
        verbose_name="更新时间",
        auto_now=True,
    )
    # 书籍状态选择
    STATUS_CHOICES = (
        ("serializing", "连载中"),
        ("completed", "已完结"),
        ("draft", "未发布"),
    )
    # 书籍状态
    status: CharField = CharField(
        verbose_name="书籍状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default="draft",
    )
    # 书籍属性
    attributes: JSONField = JSONField(
        verbose_name="书籍属性",
        help_text='存储书籍的属性, 如: {"is_top": false, "is_hot": true}',
        default=dict,
        blank=True,
    )

    @property
    def authors(self) -> UserManager[User]:
        """获取书籍的所有创作者(主创和共创)"""
        return User.objects.filter(userbookrelation__book=self, userbookrelation__creative_role__in=["author", "co_author"]).distinct()

    @property
    def main_author(self) -> Any | None:
        """获取书籍的主创"""
        relation = self.user_relations.filter(creative_role="author").first()  # type: ignore
        return relation.user if relation else None

    @property
    def average_rating(self) -> Any | Literal[0]:
        """计算书籍的平均评分(排除空评分)"""
        result = self.user_relations.exclude(rating__isnull=True).aggregate(Avg("rating"))  # type: ignore
        return result["rating__avg"] or 0

    @property
    def rating_count(self) -> int:
        """获取评分数量"""
        return self.user_relations.exclude(rating__isnull=True).count()  # type: ignore

    def __str__(self) -> str:
        return f"《{self.title}》"

    class Meta:
        verbose_name: str = "书籍"
        verbose_name_plural: str = "书籍"
        # 按时间倒序
        ordering: List[str] = ["-create_time"]


class UserBookRelation(Model):
    """用户与书籍关系模型, 整合多种关系状态"""

    # 关联书籍
    book: ForeignKey = ForeignKey(
        Book,
        on_delete=CASCADE,
        verbose_name="书籍",
        related_name="user_relations",
    )
    # 关联用户
    user: ForeignKey = ForeignKey(
        User,
        verbose_name="用户",
        on_delete=CASCADE,
    )
    # 创作关系
    CREATIVE_ROLE_CHOICES: Tuple = (
        ("reader", "读者"),
        ("author", "主创"),
        ("co_author", "共创"),
        ("editor", "编辑"),
    )
    creative_role: CharField = CharField(
        verbose_name="创作关系",
        max_length=16,
        choices=CREATIVE_ROLE_CHOICES,
        default="reader",
    )
    # 收藏状态
    COLLECTION_STATUS_CHOICES: Tuple = (
        ("not_collected", "未收藏"),
        ("collected", "已收藏"),
        ("want_to_read", "想要读"),
        ("reading", "正在读"),
        ("read", "已读完"),
    )
    collection_status: CharField = CharField(
        verbose_name="收藏状态",
        max_length=16,
        choices=COLLECTION_STATUS_CHOICES,
        default="not_collected",
    )
    # 评分(-5 到 5 分)
    rating: IntegerField = IntegerField(
        verbose_name="评分",
        validators=[
            MinValueValidator(-5),
            MaxValueValidator(5),
        ],
        default=0,
    )

    def __str__(self) -> str:
        return f"《{self.book.title}》- {self.user.username}"

    class Meta:
        verbose_name: str = "书籍-用户关系"
        verbose_name_plural: str = "书籍-用户关系"
        # 同一用户对同一书籍只能有一条关系记录
        unique_together: Tuple = ("book", "user")


class Chapter(Model):
    """章节模型, 存储书籍的章节内容"""

    # 自增主键
    id = AutoField(
        primary_key=True,
    )
    # 所属书籍
    book: ForeignKey = ForeignKey(
        Book,
        verbose_name="所属书籍",
        on_delete=CASCADE,
        related_name="chapters",
    )
    # 章数
    chapter_number: IntegerField = IntegerField(
        verbose_name="章数",
        validators=[MinValueValidator(1)],
    )
    # 章节标题
    title: CharField = CharField(
        verbose_name="章节标题",
        max_length=128,
        default="",
    )
    # 内容(JSON格式)
    content: JSONField = JSONField(
        verbose_name="内容",
        help_text='存储章节内容, 如: [{"index": 1, "type": "text", "content": "文本内容", "style": {"color": "red", "font": "SimHei"}}]',
        default=list,
        blank=True,
    )
    # 创建时间
    create_time: DateTimeField = DateTimeField(
        verbose_name="创建时间",
        default=timezone.now,
    )
    # 更新时间
    update_time: DateTimeField = DateTimeField(
        verbose_name="更新时间",
        auto_now=True,
    )
    # 章节状态
    STATUS_CHOICES: Tuple = (
        ("draft", "草稿"),
        ("published", "已发布"),
    )
    status: CharField = CharField(
        verbose_name="章节状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default="draft",
    )

    def __str__(self) -> str:
        return f"《{self.book.title}》 - 第{self.chapter_number}章: {self.title}"

    class Meta:
        verbose_name: str = "章节"
        verbose_name_plural: str = "章节"
        # 先按章数升序, 再按创建时间升序
        ordering: List[str] = ["chapter_number", "create_time"]
        # 确保同一书籍中章数唯一
        unique_together: Tuple = ("book", "chapter_number")
