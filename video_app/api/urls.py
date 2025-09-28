from django.urls import path
from video_app.api.views import VideoListView, VideoStreamView


urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', VideoStreamView.as_view(), name='video-stream'),
]
