import django_rq
import logging                                 
from django.apps import apps                   
from django.db.models.signals import post_save 
from django.dispatch import receiver           
from video_app.models import Video
from video_app.tasks import transcode_to_hls

logger = logging.getLogger(__name__)           
Video = apps.get_model('video_app', 'Video')   

@receiver(post_save, sender=Video)             
def video_post_save(sender, instance, created, **kwargs):
    """Log when a Video instance is saved or created"""
    logger.info('Video saved (id=%s, created=%s)', getattr(instance, 'id', None), created)


@receiver(post_save, sender=Video)
def enqueue_transcode(sender, instance: Video, created, **kwargs):
    """After a new Video is uploaded, enqueue transcoding job"""
    if created and instance.file:
        queue = django_rq.get_queue("default")
        queue.enqueue(transcode_to_hls, instance.id, instance.file.path)