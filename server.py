from flask import Flask, request, send_file, jsonify, Response
import yt_dlp
import os
import sys
import tempfile
import re
import threading
import uuid
import json
import queue

# Resolve base directory
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')

# ── Active download tracking ──────────────────────────────────────────────────
active_downloads = {}   # download_id -> { 'cancelled': bool, 'queue': Queue }
downloads_lock   = threading.Lock()

def is_youtube(url):
    return bool(re.search(r'(youtube\.com|youtu\.be)', url or ''))

def get_downloads_folder():
    return os.path.join(os.path.expanduser('~'), 'Downloads')

def fmt_bytes(b):
    if b is None: return '?'
    if b < 1024: return f'{b} B'
    if b < 1024**2: return f'{b/1024:.1f} KB'
    if b < 1024**3: return f'{b/1024**2:.1f} MB'
    return f'{b/1024**3:.2f} GB'

def fmt_speed(s):
    if s is None: return '?/s'
    return fmt_bytes(s) + '/s'

@app.route('/')
def index():
    return send_file(os.path.join(BASE_DIR, 'yt-downloader.html'))

@app.route('/favicon.ico')
def favicon():
    ico = os.path.join(BASE_DIR, 'Logo.ico')
    if os.path.exists(ico): return send_file(ico, mimetype='image/x-icon')
    return '', 204

@app.route('/api/cancel', methods=['POST'])
def cancel_download():
    data        = request.json or {}
    download_id = data.get('download_id')
    with downloads_lock:
        if download_id in active_downloads:
            active_downloads[download_id]['cancelled'] = True
    return jsonify({'status': 'cancelled'})

# ── SSE progress stream ───────────────────────────────────────────────────────
@app.route('/api/progress/<download_id>')
def progress_stream(download_id):
    def generate():
        q = None
        with downloads_lock:
            entry = active_downloads.get(download_id)
            if entry: q = entry['queue']
        if q is None:
            yield 'data: {"type":"error","message":"Not found"}\n\n'
            return
        while True:
            try:
                msg = q.get(timeout=60)
                yield f'data: {json.dumps(msg)}\n\n'
                if msg.get('type') in ('done', 'error', 'cancelled'):
                    break
            except Exception:
                break
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

# ── Download endpoint ─────────────────────────────────────────────────────────
@app.route('/api/download', methods=['POST'])
def download():
    data        = request.json
    url         = data.get('url')
    fmt         = data.get('format', 'mp4')
    resolution  = data.get('resolution', 'best')
    codec       = data.get('codec', 'vp9')
    acodec      = data.get('acodec', 'aac')
    bitrate     = data.get('bitrate', '320')
    site_mode   = data.get('site_mode', False)
    download_id = data.get('download_id', str(uuid.uuid4()))

    if not url: return jsonify({'error': 'No URL provided'}), 400

    out_dir     = get_downloads_folder()
    ffmpeg_path = os.path.join(BASE_DIR, 'ffmpeg.exe')
    use_ffmpeg  = ffmpeg_path if os.path.exists(ffmpeg_path) else None

    # Set up progress queue
    q = queue.Queue()
    with downloads_lock:
        active_downloads[download_id] = {'cancelled': False, 'queue': q}

    def is_cancelled():
        with downloads_lock:
            return active_downloads.get(download_id, {}).get('cancelled', False)

    # ── Build format string ───────────────────────────────────────────────────
    if site_mode:
        res = resolution if resolution != 'best' else None
        format_str = (f'bestvideo[height<={res}]+bestaudio/best[height<={res}]/best' if res else 'bestvideo+bestaudio/best')
    elif fmt == 'mp3':
        format_str = 'bestaudio/best'
    elif resolution == 'best':
        format_str = 'bestvideo+bestaudio/best'
    else:
        codec_map  = {'h264': 'avc1', 'h265': 'hvc1', 'vp9': 'vp9', 'av1': 'av01'}
        vcodec     = codec_map.get(codec, 'vp9')
        format_str = (
            f'bestvideo[height<={resolution}][vcodec~="{vcodec}"]+bestaudio/'
            f'bestvideo[height<={resolution}]+bestaudio/'
            f'best[height<={resolution}]/best'
        )

    out_fmt = 'mp4' if site_mode else (fmt if fmt != 'mp3' else None)

    ydl_opts = {
        'format': format_str,
        'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
        'merge_output_format': out_fmt,
        'overwrites': True,
        'no_cache_dir': True,
        'postprocessors': [],
        'noprogress': False,
    }
    if use_ffmpeg: ydl_opts['ffmpeg_location'] = use_ffmpeg
    if not site_mode and fmt == 'mp3':
        ydl_opts['postprocessors'].append({
            'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': bitrate,
        })

    # ── Progress hook → push to queue ────────────────────────────────────────
    def progress_hook(d):
        if is_cancelled():
            raise yt_dlp.utils.DownloadCancelled('Cancelled by user')

        status = d.get('status')
        if status == 'downloading':
            downloaded  = d.get('downloaded_bytes', 0)
            total       = d.get('total_bytes') or d.get('total_bytes_estimate')
            speed       = d.get('speed')
            percent     = (downloaded / total * 100) if total else None

            q.put({
                'type':        'progress',
                'percent':     round(percent, 1) if percent is not None else None,
                'downloaded':  fmt_bytes(downloaded),
                'total':       fmt_bytes(total),
                'speed':       fmt_speed(speed),
                'downloaded_raw': downloaded,
                'total_raw':   total,
            })

        elif status == 'finished':
            q.put({'type': 'merging', 'message': 'Merging video & audio…'})

    ydl_opts['progress_hooks'] = [progress_hook]

    # Run in background thread so SSE can stream while downloading
    def run_download():
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if is_cancelled(): q.put({'type': 'cancelled'}); return
                info       = ydl.extract_info(url, download=True)
                title      = info.get('title', 'download')
                safe_title = yt_dlp.utils.sanitize_filename(title)

            if is_cancelled(): q.put({'type': 'cancelled'}); return

            ext      = ('mp3' if (not site_mode and fmt == 'mp3') else (out_fmt or 'mp4'))
            filepath = os.path.join(out_dir, f'{safe_title}.{ext}')
            if not os.path.exists(filepath):
                for f in sorted(os.listdir(out_dir), key=lambda x: -os.path.getmtime(os.path.join(out_dir, x))):
                    if f.endswith(f'.{ext}'):
                        filepath = os.path.join(out_dir, f); break

            q.put({'type': 'done', 'filename': os.path.basename(filepath), 'path': filepath})

        except yt_dlp.utils.DownloadCancelled:
            q.put({'type': 'cancelled'})
        except Exception as e:
            if is_cancelled(): q.put({'type': 'cancelled'})
            else: q.put({'type': 'error', 'message': str(e)})
        finally:
            with downloads_lock: active_downloads.pop(download_id, None)

    t = threading.Thread(target=run_download, daemon=True)
    t.start()

    # Return immediately — client listens on /api/progress/<id> via SSE
    return jsonify({'status': 'started', 'download_id': download_id})


if __name__ == '__main__':
    app.run(port=5000, debug=False, threaded=True)
