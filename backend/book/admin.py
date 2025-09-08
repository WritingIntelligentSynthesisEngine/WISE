# book/admin.py
from django.contrib import admin

from book.models import Category, Book, UserBookRelation, Chapter

# Register your models here.
admin.site.register(Category)
admin.site.register(Book)
admin.site.register(UserBookRelation)
admin.site.register(Chapter)

admin.site.site_header = "AllBookCloud"
admin.site.site_title = "书云 MIS"
admin.site.index_title = "欢迎使用书云管理员后台系统"
