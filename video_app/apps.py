from django.apps import AppConfig  

class VideoAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  
    name = 'video_app'                                    
    verbose_name = 'Videos'  

    def ready(self):
        """Import signals when app registry is ready"""
        import video_app.signals  
        
