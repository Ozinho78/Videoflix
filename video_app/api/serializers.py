from rest_framework import serializers
from video_app.models import Video

class VideoSerializer(serializers.ModelSerializer):
    """Serializer to convert Video model instances to JSON"""
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'created_at', 'title', 'description', 'thumbnail_url', 'category']
        read_only_fields = ['id', 'created_at', 'thumbnail_url']

    def get_thumbnail_url(self, obj):
        """Return absolute thumbnail URL or None if missing"""
        request = self.context.get('request')
        if obj.thumbnail and hasattr(obj.thumbnail, 'url'):
            return request.build_absolute_uri(obj.thumbnail.url) # http://127.0.0.1:8000/media/thumbnails/1.jpg
        return None