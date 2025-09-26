from django.db import models  # Base ORM types

def video_upload_path(instance, filename):
    """Upload all videos directly into MEDIA_ROOT/videos/"""
    # Using id in path is nice after the instance exists; for first save it's None -> fallback.
    return f'videos/{filename}'

class Video(models.Model):
    """Stores an uploaded video file and basic metadata."""
    # Short title for admin list/search
    title = models.CharField(max_length=200, help_text='Short display title')
    # Optional description field
    description = models.TextField(blank=True, help_text='Optional description')
    # Raw uploaded file (you can later create HLS renditions via RQ/Celery)
    file = models.FileField(upload_to=video_upload_path, help_text='Upload the original video file')
    # Timestamps for ordering/filtering
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the Video model."""
        ordering = ('-created_at',)  # Default ordering: newest first
        verbose_name = 'Video'       # Singular name in admin
        verbose_name_plural = 'Videos'  # Plural name in admin

    def __str__(self):
        """Human-readable representation in admin dropdowns etc."""
        return self.title or f'Video #{self.pk}'
