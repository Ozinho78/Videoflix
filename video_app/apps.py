from django.apps import AppConfig


class VideoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'video_app'
    
    def ready(self):
        import video_app.signals  # noqa: F401
        # return super().ready() # Import signals module to connect signal handlers
