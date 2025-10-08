"""Endpoints for video app"""
from django.urls import path
from video_app.api.views import VideoListView, VideoStreamView, VideoSegmentView


urlpatterns = [
    path('video/', VideoListView.as_view(), name='video-list'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', VideoStreamView.as_view(), name='video-stream'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>', VideoSegmentView.as_view(), name='video-segment'),
]
