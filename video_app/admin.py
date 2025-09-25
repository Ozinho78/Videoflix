from django.contrib import admin               # Admin site utilities
from .models import Video                      # Import the Video model to register it

@admin.register(Video)                         # Register model via decorator
class VideoAdmin(admin.ModelAdmin):
    """Admin configuration for Video model."""
    # Columns in change list
    list_display = ('id', 'title', 'created_at', 'updated_at')
    # Enable simple search
    search_fields = ('title', 'description')
    # Sidebar filter
    list_filter = ('created_at',)
    # Default ordering
    ordering = ('-created_at',)
    # Fields layout (optional; keeps form tidy)
    fieldsets = (
        ('Primary Info', {'fields': ('title', 'description')}),
        ('File', {'fields': ('file',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    # Make timestamps read-only in admin form
    readonly_fields = ('created_at', 'updated_at')
