from rest_framework import generics, permissions
from video_app.models import Video
from video_app.api.serializers import VideoSerializer


class VideoListView(generics.ListAPIView):
    """
    Return a list of all available videos.
    Requires JWT authentication.
    """
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]
