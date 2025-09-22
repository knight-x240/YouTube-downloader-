import yt_dlp
import os

def get_formats(url):
    ydl_opts = {'quiet': True, 'skip_download': True}
    formats = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        for f in info_dict.get('formats', []):
            vcodec = f.get('vcodec')
            acodec = f.get('acodec')
            ext = f.get('ext')
            format_note = f.get('format_note', f.get('height', ''))
            filesize = f.get('filesize') or f.get('filesize_approx', 0)
            # Video+audio
            if vcodec != 'none' and acodec != 'none':
                formats.append({
                    'type': 'video',
                    'quality': format_note,
                    'ext': ext,
                    'format_id': f['format_id'],
                    'filesize': filesize
                })
            # Audio-only
            elif vcodec == 'none' and acodec != 'none':
                abr = f.get('abr', '')
                formats.append({
                    'type': 'audio',
                    'quality': f"{abr}kbps" if abr else format_note,
                    'ext': ext,
                    'format_id': f['format_id'],
                    'filesize': filesize
                })
    # Remove duplicates based on format_id
    unique_formats = {f['format_id']: f for f in formats}
    # Sort: video by resolution descending, audio by bitrate descending
    video_formats = [f for f in unique_formats.values() if f['type']=='video']
    audio_formats = [f for f in unique_formats.values() if f['type']=='audio']
    video_formats = sorted(video_formats, key=lambda x: int(x['quality'].replace('p','').replace('hd','').replace('sd','').replace('audio','0')), reverse=True)
    audio_formats = sorted(audio_formats, key=lambda x: int(str(x['quality']).replace('kbps','').replace('audio','0')), reverse=True)
    return video_formats + audio_formats

def download_media(url, format_id, choice):
    if choice == "audio":
        ydl_opts = {
            'format': format_id,
            'outtmpl': 'audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True
        }
        ext = 'mp3'
        outname = 'audio.' + ext
    else:
        ydl_opts = {
            'format': format_id,
            'outtmpl': 'video.%(ext)s',
            'quiet': True
        }
        ext = 'mp4'
        outname = 'video.' + ext
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        if choice == "audio":
            # yt-dlp will postprocess to mp3
            filename = os.path.splitext(filename)[0] + ".mp3"
        else:
            if not filename.endswith(".mp4"):
                filename = os.path.splitext(filename)[0] + ".mp4"
    return filename