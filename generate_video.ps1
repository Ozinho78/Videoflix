# Ordner vorbereiten
mkdir -p media/hls/3/480p media/hls/3/720p media/hls/3/1080p

# 480p
ffmpeg -i media/videos/test.mp4 \
  -vf scale=-2:480 -c:v h264 -c:a aac \
  -f hls -hls_time 2 -hls_playlist_type vod media/hls/3/480p/index.m3u8

# 720p
ffmpeg -i media/videos/test.mp4 \
  -vf scale=-2:720 -c:v h264 -c:a aac \
  -f hls -hls_time 2 -hls_playlist_type vod media/hls/3/720p/index.m3u8

# 1080p
ffmpeg -i media/videos/test.mp4 \
  -vf scale=-2:1080 -c:v h264 -c:a aac \
  -f hls -hls_time 2 -hls_playlist_type vod media/hls/3/1080p/index.m3u8
