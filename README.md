# YouTube Downloader & MP3 Tagger

A robust Python script to download YouTube playlists (or single videos), convert them to high-quality MP3 files with configurable bitrates, embed video thumbnails as album art, and apply clean ID3 tags (artist, title, album, and track number).

## Features

- **Playlist Support**: Downloads entire playlists and preserves their order using track indices.
- **Audio Extraction**: Extracts high-quality audio streams and converts them to MP3.
- **Configurable Bitrate**: Choose from standard bitrates (`96`, `128`, `160`, `192`, `256`, `320` kbps). Default is `192` kbps.
- **Automatic ID3 Tagging**:
  - **Title & Artist**: Automatically extracts and cleans video titles (e.g. splits `"Artist - Song (Official Video)"` into Artist: `"Artist"` and Title: `"Song"`).
  - **Album**: Uses the playlist title as the MP3 Album name.
  - **Track Number**: Preserves playlist ordering as ID3 track numbers.
  - **Artwork**: Automatically embeds the YouTube video thumbnail as the MP3 album cover.
- **Visuals**: Output styled with ANSI colors for clear command-line tracking.

## Prerequisites

- **Python 3.7+**
- **FFmpeg**: Required by `yt-dlp` for audio extraction and thumbnail embedding.
  - *macOS*: Install via Homebrew: `brew install ffmpeg`
  - *Linux*: Install via apt: `sudo apt install ffmpeg`

## Installation

1. **Clone or navigate** to the repository:
   ```bash
   cd Youtube_Downloader
   ```

2. **Create a virtual environment** and activate it:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the script by providing the YouTube video or playlist URL:

```bash
python3 downloader.py "PLAYLIST_OR_VIDEO_URL"
```

### Options

- `-b`, `--bitrate`: Target MP3 bitrate in kbps. Choose from `96`, `128`, `160`, `192`, `256`, or `320`. (Default: `192`)
- `-o`, `--output`: Target folder where downloaded MP3s will be saved. (Default: `downloads`)
- `--no-artwork`: Disable downloading and embedding video thumbnails as album artwork.
- `--raw-metadata`: Disable automatic metadata cleaning (keeps the raw YouTube video title and uploader).
- `--no-index`: Disable prefixing filenames with the playlist index.

### Examples

**Download a playlist at default settings (192 kbps, output to `downloads/`):**
```bash
python3 downloader.py "https://www.youtube.com/playlist?list=PL4fGSI1pDJn5nwy17B6nfa7oqNez8u4K7"
```

**Download a playlist at high quality (320 kbps) to a custom folder:**
```bash
python3 downloader.py "https://www.youtube.com/playlist?list=PL4fGSI1pDJn5nwy17B6nfa7oqNez8u4K7" -b 320 -o "~/Music/RippedPlaylist"
```

**Download a single video without downloading artwork:**
```bash
python3 downloader.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --no-artwork
```
