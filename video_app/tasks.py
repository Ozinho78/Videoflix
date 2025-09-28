import subprocess
import os
from django.conf import settings


def transcode_to_hls(video_id: int, input_path: str):
    """
    Transcode a video file into multiple HLS renditions (480p, 720p, 1080p).
    Creates directories: media/hls/<video_id>/<resolution>/index.m3u8
    """
    base_dir = os.path.join(settings.MEDIA_ROOT, "hls", str(video_id))
    os.makedirs(base_dir, exist_ok=True)

    renditions = {
        "480p": "scale=-2:480",
        "720p": "scale=-2:720",
        "1080p": "scale=-2:1080",
    }

    for res, scale in renditions.items():
        out_dir = os.path.join(base_dir, res)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, "index.m3u8")

        cmd = [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", scale, "-c:v", "h264", "-c:a", "aac",
            "-f", "hls", "-hls_time", "4", "-hls_playlist_type", "vod", out_path
        ]
        subprocess.run(cmd, check=True)



# import subprocess
# def convert720p(source):
# new_file_name = # TODO - Alter name + _720p.mp4
# cmd = 'ffmpeg -i "{}" -s hd720 -c:v libx264 -crf 23 -c:a aac -strict -2 "{}"'.format(source, new_file)
# run = subprocess.run(cmd, capture_output=True)