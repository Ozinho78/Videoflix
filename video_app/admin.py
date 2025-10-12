
from django.contrib import admin
from video_app.models import Video

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video model."""
    list_display = ('id', 'title', 'category', 'created_at', 'updated_at')  
    search_fields = ('title', 'description', 'category')
    list_filter = ('created_at', 'category')
    ordering = ('-created_at',)
    fieldsets = (
        ('Primary Info', {'fields': ('title', 'description', 'category')}),
        ('Media', {'fields': ('file', 'thumbnail')}),
        # ('File', {'fields': ('file',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def has_thumbnail(self, obj):
        """Show ✓ if a thumbnail exists."""
        return bool(obj.thumbnail)
    has_thumbnail.boolean = True
