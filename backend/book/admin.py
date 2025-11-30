# book/admin.py
from django.contrib import admin

from book.models import Category, Book, UserBookRelation, Chapter


admin.site.register(Category)
admin.site.register(Book)
admin.site.register(UserBookRelation)
admin.site.register(Chapter)
