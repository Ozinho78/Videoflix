import os
from django.http import FileResponse, Http404
from django.conf import settings
from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
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
    
    
class VideoStreamView(APIView):
    """
    Returns the HLS playlist (index.m3u8) for a given video and resolution.
    Requires JWT authentication.
    """
    permission_classes = [IsAuthenticated]
    # permission_classes = [permissions.AllowAny]

    def get(self, request, movie_id: int, resolution: str, *args, **kwargs):
        # 1) Get the video object by ID
        try:
            video = Video.objects.get(pk=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")

        # 2) Build expected path: MEDIA_ROOT/hls/<id>/<resolution>/index.m3u8
        manifest_path = os.path.join(
            settings.MEDIA_ROOT,
            'hls',
            str(video.id),
            resolution,
            'index.m3u8'
        )

        # 3) Return manifest if it exists
        if os.path.exists(manifest_path):
            return FileResponse(
                open(manifest_path, 'rb'),
                content_type='application/vnd.apple.mpegurl'
            )
        else:
            raise Http404("Manifest not found for this resolution")


class VideoSegmentView(APIView):
    """
    Returns a single HLS video segment (.ts) for a given movie and resolution.
    Requires JWT authentication.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id: int, resolution: str, segment: str, *args, **kwargs):
        # 1) Video prüfen
        try:
            video = Video.objects.get(pk=movie_id)
        except Video.DoesNotExist:
            raise Http404("Video not found")

        # 2) Pfad zum Segment bauen
        segment_path = os.path.join(
            settings.MEDIA_ROOT,
            'hls',
            str(video.id),
            resolution,
            segment
        )

        # 3) Datei liefern oder 404
        if os.path.exists(segment_path):
            return FileResponse(open(segment_path, 'rb'), content_type='video/MP2T')
        raise Http404("Segment not found")
