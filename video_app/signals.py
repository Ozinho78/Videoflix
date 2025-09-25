from .models import Video
from django.dispatch import receiver
from django.db.models.signals import post_save


@receiver(post_save, sender=Video)
def video_post_save(sender, instance, created, **kwargs):
    print('Video instance has been saved.')
    if created:
        print('A new video instance was created.')
        
        
