from django.apps import AppConfig  # Base class for app configuration

class VideoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # Default auto field type
    name = 'video_app'                                    # Python path of the app
    verbose_name = 'Videos'  # Display name in admin sidebar

    def ready(self):
        """Import signals when app registry is ready."""
        import video_app.signals  # Import signals so receivers get registered
        # No return needed; importing connects the signal handlers
