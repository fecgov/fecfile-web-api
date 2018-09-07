from django.contrib import admin
from .models import Post

class PostAdmin(admin.ModelAdmin):
    search_fields = ('content', 'author__username', 'author__email')
    ordering = ('-updated_at',)
    list_display = ('content', 'author')

admin.site.register(Post, PostAdmin)
