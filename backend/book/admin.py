# book/admin.py
from django.contrib import admin

from book.models import Category, Book, UserBookRelation, Chapter

# Register your models here.
admin.site.register(Category)
admin.site.register(Book)
admin.site.register(UserBookRelation)
admin.site.register(Chapter)

admin.site.site_header = "WISE"
admin.site.site_title = "文芯雕珑 MIS"
admin.site.index_title = "欢迎使用文芯雕珑管理员后台系统"
