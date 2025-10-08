import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from video_app.models import Video
import os


@pytest.mark.django_db
def test_segment_found(tmp_path, settings):
    """Authenticated request for existing segment returns 200 with correct content type and body"""
    User = get_user_model()
    user = User.objects.create_user(
        username='streamer@example.com',
        email='streamer@example.com',
        password='StrongP@ssw0rd',
        is_active=True
    )
    client = APIClient()
    login_url = reverse('login')
    login_resp = client.post(login_url, {'email': user.email, 'password': 'StrongP@ssw0rd'}, format='json')
    assert login_resp.status_code == 200
    video = Video.objects.create(title='SegmentTest', category='Demo', file='videos/test.mp4')
    seg_dir = tmp_path / "hls" / str(video.id) / "720p"
    seg_dir.mkdir(parents=True)
    seg_path = seg_dir / "index0.ts"
    seg_path.write_bytes(b"dummy TS content")
    settings.MEDIA_ROOT = tmp_path
    url = reverse('video-segment', args=[video.id, '720p', 'index0.ts'])
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'] == 'video/MP2T'
    body = b''.join(response.streaming_content)
    assert b"dummy TS content" in body


@pytest.mark.django_db
def test_segment_not_found(tmp_path, settings):
    """Request for non-existing segment returns 404"""
    User = get_user_model()
    user = User.objects.create_user(
        username='streamer2@example.com',
        email='streamer2@example.com',
        password='StrongP@ssw0rd',
        is_active=True
    )
    client = APIClient()
    login_url = reverse('login')
    login_resp = client.post(login_url, {'email': user.email, 'password': 'StrongP@ssw0rd'}, format='json')
    assert login_resp.status_code == 200
    video = Video.objects.create(title='MissingSegment', category='Demo', file='videos/test2.mp4')
    settings.MEDIA_ROOT = tmp_path
    url = reverse('video-segment', args=[video.id, '720p', 'missing.ts'])
    response = client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND