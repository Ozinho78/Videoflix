from django.db import models
import os


def video_upload_path(instance, filename):
    """Upload all videos directly into MEDIA_ROOT/videos/"""    
    return f'videos/{filename}'

def thumbnail_upload_path(instance, filename):
    """Store thumbnails under MEDIA_ROOT/thumbnails/<video_id>.jpg"""
    base, ext = os.path.splitext(filename)
    return f'thumbnails/{instance.id or "temp"}{ext}'

class Video(models.Model):
    """Stores an uploaded video file and basic metadata"""
    title = models.CharField(max_length=200, help_text='Short display title')
    description = models.TextField(blank=True, help_text='Optional description')
    category = models.CharField(
        max_length=100,
        help_text='Category/genre of the video',
        blank=True,
        null=True
    )
    file = models.FileField(upload_to=video_upload_path, help_text='Upload the original video file')
    thumbnail = models.ImageField(upload_to=thumbnail_upload_path, blank=True, null=True, help_text='Optional thumbnail image')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options for the Video model"""
        ordering = ('-created_at',)  
        verbose_name = 'Video'       
        verbose_name_plural = 'Videos'  

    def __str__(self):
        """Human-readable representation in admin dropdowns etc"""
        return self.title or f'Video #{self.pk}'
