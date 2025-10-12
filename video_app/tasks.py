import subprocess
import os
import logging
from django.conf import settings
from video_app.models import Video

logger = logging.getLogger(__name__)


def generate_thumbnail(video_id: int, input_path: str):
    """
    Create a single thumbnail (JPG) from the middle of the video using ffmpeg
    Saves to MEDIA_ROOT/thumbnails/<video_id>.jpg
    """
    output_dir = os.path.join(settings.MEDIA_ROOT, 'thumbnails')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{video_id}.jpg')

    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-ss', '00:00:02',
        '-vframes', '1',
        '-q:v', '2',
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        logger.info(f'Thumbnail created for video {video_id}')
        from video_app.models import Video
        video = Video.objects.get(id=video_id)
        relative_path = os.path.relpath(output_path, settings.MEDIA_ROOT)
        video.thumbnail.name = relative_path
        video.save(update_fields=['thumbnail'])
    except subprocess.CalledProcessError as e:
        logger.error(f'Failed to create thumbnail for {video_id}: {e.stderr.decode()}')


def transcode_to_hls(video_id: int, input_path: str):
    """
    Transcode a video file into multiple HLS renditions (480p, 720p, 1080p)
    Creates directories: media/hls/<video_id>/<resolution>/index.m3u8
    """
    logger.info(f'Starting HLS transcoding for video {video_id}: {input_path}')
    base_dir = os.path.join(settings.MEDIA_ROOT, 'hls', str(video_id))
    os.makedirs(base_dir, exist_ok=True)
    renditions = {
        '480p': {'scale': 'scale=-2:480', 'bitrate': '800k'},
        '720p': {'scale': 'scale=-2:720', 'bitrate': '2500k'},
        '1080p': {'scale': 'scale=-2:1080', 'bitrate': '5000k'},
    }
    for res, params in renditions.items():
        out_dir = os.path.join(base_dir, res)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'index.m3u8')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-vf', params['scale'],
            '-c:v', 'libx264',
            '-b:v', params['bitrate'],
            '-c:a', 'aac',
            '-f', 'hls',
            '-hls_time', '4',
            '-hls_playlist_type', 'vod',
            '-hls_segment_filename', os.path.join(out_dir, 'segment_%03d.ts'),
            out_path,
        ]
        logger.debug(f'Running ffmpeg for {res}: {" ".join(cmd)}')
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f'Successfully transcoded {res} for video {video_id}')
        except subprocess.CalledProcessError as e:
            logger.error(f'Error transcoding {res} for video {video_id}: {e.stderr.decode()}')
    logger.info(f'Completed transcoding for video {video_id}')
    generate_thumbnail(video_id, input_path)
