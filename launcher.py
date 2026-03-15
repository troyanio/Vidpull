import sys
import os
import shutil
import tempfile
import logging
import ctypes

# ── Version tag — bump to force re-extraction on update ──────────────────────
APP_VERSION    = '1.0.0'
CACHE_DIR_NAME = f'Vidpull_cache_{APP_VERSION}'

def get_cache_dir():
    return os.path.join(tempfile.gettempdir(), CACHE_DIR_NAME)

def is_frozen():
    return getattr(sys, 'frozen', False)

def get_source_dir():
    return sys._MEIPASS if is_frozen() else os.path.dirname(os.path.abspath(__file__))

def needs_extraction(cache_dir):
    if not os.path.isdir(cache_dir):
        return True
    for f in ['server.py', 'yt-downloader.html', 'Logo.ico']:
        if not os.path.exists(os.path.join(cache_dir, f)):
            return True
    marker = os.path.join(cache_dir, '.version')
    if not os.path.exists(marker):
        return True
    with open(marker) as f:
        return f.read().strip() != APP_VERSION

def copy_to_cache(source_dir, cache_dir):
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir, ignore_errors=True)
    shutil.copytree(source_dir, cache_dir)
    with open(os.path.join(cache_dir, '.version'), 'w') as f:
        f.write(APP_VERSION)

# ── Cache check / extraction ──────────────────────────────────────────────────
cache_dir = get_cache_dir()
if is_frozen() and needs_extraction(cache_dir):
    copy_to_cache(get_source_dir(), cache_dir)

os.chdir(cache_dir)
sys.path.insert(0, cache_dir)

# ── Get screen size via Windows API (no tkinter needed) ───────────────────────
def get_window_size():
    try:
        # Get true physical screen size accounting for DPI scaling
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
    except Exception:
        # Fallback if something goes wrong
        screen_w, screen_h = 1920, 1080

    if screen_h >= 2160:       # 4K
        w, h = 860, int(screen_h * 0.72)
    elif screen_h >= 1440:     # 1440p
        w, h = 820, int(screen_h * 0.80)
    else:                      # 1080p and below
        w, h = 780, int(screen_h * 0.88)

    h = min(h, screen_h - 80)
    h = max(h, 700)
    return w, h

w, h = get_window_size()

# ── Suppress Flask output ─────────────────────────────────────────────────────
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# ── Launch ────────────────────────────────────────────────────────────────────
from server import app as flask_app
from flaskwebgui import FlaskUI

ui = FlaskUI(
    app=flask_app,
    server='flask',
    width=w,
    height=h,
    port=5000,
)

ui.run()
