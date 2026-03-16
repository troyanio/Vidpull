# Vidpull

A Windows desktop app for downloading videos from YouTube, Instagram, 
Twitter, Twitch, TikTok, Reddit and 1000+ other sites. Paste a link, 
pick your settings, download. Files go straight to your Downloads folder.

---

## Download

- **[Vidpull_Setup.exe](https://github.com/troyanio/Vidpull/releases/download/v1.0.0/Vidpull_Setup.exe)** — installs to Program Files, creates a desktop shortcut
- **[Vidpull_Portable.exe](https://github.com/troyanio/Vidpull/releases/download/v1.0.0/Vidpull_Portable.exe)** — single file, no install needed, just run it

---

## What it does

- Downloads from YouTube, Instagram, Twitter/X, Twitch, TikTok, Reddit and 1000+ sites
- For YouTube you can pick the resolution, video codec (H.264 / H.265 / VP9 / AV1),
  audio codec (AAC / Opus / MP3 / FLAC) and format (MP4 / MP3 / WEBM)
- For everything else it automatically grabs the best quality available
- Shows live download speed, file size and progress while downloading
- Files save directly to your Downloads folder
- Quick presets — Best Quality, Balanced, Compatible
- App color theme changes based on the site you paste
- FFmpeg is bundled — nothing extra to install

---

## Stack

- **yt-dlp** — handles actually downloading from 1000+ sites
- **FFmpeg** — merges video/audio streams and converts formats, bundled into the app
- **Flask** — runs a local web server in the background on port 5000
- **flaskwebgui** — opens the Flask app in a Chrome/Edge app-mode window so it looks like a desktop app
- **HTML/CSS/JS** — the entire UI is one self-contained HTML file served by Flask
- **Server-Sent Events** — streams live progress (speed, size, percent) from Flask to the UI
- **PyInstaller** — bundles everything into a standalone exe
- **Inno Setup** — wraps the PyInstaller output into a proper Windows installer

---

## Building from source

**Requirements**
- Python 3.10+
- FFmpeg — download from ffmpeg.org, add the bin folder to your PATH
- Git

**Install dependencies**
```
pip install yt-dlp flask flaskwebgui pyinstaller
```

**Run in dev mode**
```
python launcher.py
```

**Build the exe (installer version)**
```
pyinstaller --onedir --noconsole --icon="logo.ico" ^
  --add-data "yt-downloader.html;." ^
  --add-data "server.py;." ^
  --add-data "logo.ico;." ^
  --add-binary "C:\path\to\ffmpeg.exe;." ^
  --hidden-import=yt_dlp --hidden-import=flask --hidden-import=flaskwebgui ^
  --hidden-import=werkzeug --hidden-import=jinja2 --hidden-import=click ^
  --hidden-import=email --hidden-import=email.mime ^
  --collect-all yt_dlp --collect-all flask --collect-all flaskwebgui ^
  --collect-all werkzeug --collect-all jinja2 --collect-all click ^
  --name "Vidpull" launcher.py
```

**Build the portable single exe**

Same command but replace `--onedir` with `--onefile` and `--name "Vidpull"` 
with `--name "Vidpull_Portable"`

**Build the installer**

Install Inno Setup from jrsoftware.org, open `installer.iss` and press F9.
Output will be in the `installer_output` folder.

---

*For personal use only. Respect copyright and each site's terms of service.*
```
