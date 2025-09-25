import logging                                 # Use Django/Python logging
from django.apps import apps                   # Lazy access to models by app_label, model_name
from django.db.models.signals import post_save # Signal emitted after model save
from django.dispatch import receiver           # Decorator to register handlers

logger = logging.getLogger(__name__)           # Module-level logger

# Get the model lazily to avoid import-time race conditions
Video = apps.get_model('video_app', 'Video')   # app_label, ModelName

@receiver(post_save, sender=Video)             # Connect to post_save for Video
def video_post_save(sender, instance, created, **kwargs):
    """Log when a Video instance is saved or created."""
    logger.info('Video saved (id=%s, created=%s)', getattr(instance, 'id', None), created)
