from rest_framework import serializers
from video_app.models import Video

class VideoSerializer(serializers.ModelSerializer):
    """Serializer to convert Video model instances to JSON."""
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']
        read_only_fields = ['id', 'created_at', 'thumbnail_url']

    def get_thumbnail_url(self, obj):
        """Build absolute URL for thumbnail (placeholder for now)."""
        request = self.context.get('request')
        # You might later add a real thumbnail field; here we just return file URL
        if obj.file and hasattr(obj.file, 'url'):
            return request.build_absolute_uri(obj.file.url)
        return None
