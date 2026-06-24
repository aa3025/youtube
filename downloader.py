#!/usr/bin/env python3
import os
import sys
import re
import argparse
import yt_dlp
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, ID3NoHeaderError

# ANSI Escape Sequences for terminal styling
COLOR_HEADER = "\033[95m"
COLOR_BLUE = "\033[94m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"

def log_info(message):
    print(f"{COLOR_BLUE}[INFO]{COLOR_RESET} {message}")

def log_success(message):
    print(f"{COLOR_GREEN}[SUCCESS]{COLOR_RESET} {message}")

def log_warning(message):
    print(f"{COLOR_YELLOW}[WARNING]{COLOR_RESET} {message}")

def log_error(message):
    print(f"{COLOR_RED}[ERROR]{COLOR_RESET} {message}")

def clean_title_artist(video_title, uploader):
    """
    Cleans up video titles and extracts artist/title if they are in the 'Artist - Title' format.
    Also strips out common YouTube video title suffixes.
    """
    artist = uploader
    title = video_title

    # Try splitting by common separators like ' - ', ' – ', ' — '
    parts = re.split(r'\s+-\s+|\s+–\s+|\s+—\s+', video_title, maxsplit=1)
    if len(parts) == 2:
        artist = parts[0].strip()
        title = parts[1].strip()

    # Common YouTube title clutter patterns
    clutter_patterns = [
        r'\s*[([（【]Official\s*(?:Music)?\s*(?:Video|Audio|Lyrics|Visualizer)?\s*[)\]）】]',
        r'\s*[([（【]Music\s*Video\s*[)\]）】]',
        r'\s*[([（【]Lyric\s*Video\s*[)\]）】]',
        r'\s*[([（【]Audio\s*[)\]）】]',
        r'\s*[([（【]4K\s*Ultra\s*HD\s*[)\]）】]',
        r'\s*[([（【]HD\s*[)\]）】]',
        r'\s*[([（【]\s*HQ\s*\s*[)\]）】]',
        r'\s*[([（【]\s*Explicit\s*\s*[)\]）】]',
        r'\s*[([（【]1080p\s*[)\]）】]',
        r'\s*[([（【]Official\s*[)\]）】]',
        r'\s*\|\s*Official\s*Music\s*Video\s*$',
        r'\s*\|\s*Official\s*Video\s*$',
        r'\s*\|\s*Music\s*Video\s*$',
    ]
    for pattern in clutter_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        artist = re.sub(pattern, '', artist, flags=re.IGNORECASE)

    # Clean up double spaces, leading/trailing whitespace, and quotes
    title = re.sub(r'\s+', ' ', title).strip().strip('"').strip("'")
    artist = re.sub(r'\s+', ' ', artist).strip().strip('"').strip("'")

    return artist, title

class ID3TaggerPostProcessor(yt_dlp.postprocessor.PostProcessor):
    """
    Custom yt-dlp post-processor to apply mutagen ID3 tags and clean up metadata
    after the conversion to MP3 is complete.
    """
    def __init__(self, playlist_title=None, clean_metadata=True):
        super().__init__()
        self.playlist_title = playlist_title
        self.clean_metadata = clean_metadata

    def run(self, information):
        filepath = information.get('filepath')
        if not filepath or not filepath.endswith('.mp3'):
            return [], information

        try:
            # Ensure the MP3 file has ID3 tags initialized
            try:
                audio = EasyID3(filepath)
            except ID3NoHeaderError:
                tags = ID3()
                tags.save(filepath)
                audio = EasyID3(filepath)

            # Extract raw fields from yt-dlp info
            raw_title = information.get('title', 'Unknown Title')
            raw_uploader = information.get('uploader', 'Unknown Artist')
            
            # Use metadata cleaning or fall back to raw values
            if self.clean_metadata:
                artist, title = clean_title_artist(raw_title, raw_uploader)
            else:
                artist, title = raw_uploader, raw_title

            # Fallback to playlist name for Album, or default
            album = self.playlist_title or information.get('playlist_title') or 'YouTube Downloads'
            tracknumber = str(information.get('playlist_index') or '')

            # Apply ID3 tags
            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            if tracknumber:
                audio['tracknumber'] = tracknumber
                
            audio.save()
            log_success(f"Tagged metadata for: '{title}' by '{artist}' (Track {tracknumber if tracknumber else 'N/A'}, Album: '{album}')")
        except Exception as e:
            log_warning(f"Failed to tag metadata for {filepath}: {str(e)}")

        return [], information

def download_playlist(url, bitrate, output_dir, no_artwork, clean_metadata, no_playlist_indexing):
    """
    Configures yt-dlp and downloads the playlist/video.
    """
    # 1. Fetch playlist metadata first to get playlist title
    log_info("Fetching playlist/video metadata...")
    ydl_opts_meta = {
        'extract_flat': True,
        'ignoreerrors': True,
    }
    
    playlist_title = None
    is_playlist = False
    with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            if info:
                if info.get('_type') == 'playlist':
                    is_playlist = True
                    playlist_title = info.get('title')
                    if playlist_title:
                        log_info(f"Target Playlist Album Name: {COLOR_BOLD}{playlist_title}{COLOR_RESET}")
                else:
                    log_info(f"Target Video Title: {COLOR_BOLD}{info.get('title')}{COLOR_RESET}")
        except Exception as e:
            log_warning(f"Could not retrieve metadata upfront: {e}")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 2. Configure yt-dlp options
    # Output template: include index if downloading a playlist, otherwise just title
    if no_playlist_indexing or not is_playlist:
        out_tmpl = os.path.join(output_dir, '%(title)s.%(ext)s')
    else:
        out_tmpl = os.path.join(output_dir, '%(playlist_index)s - %(title)s.%(ext)s')

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_tmpl,
        'ignoreerrors': True,
        'writethumbnail': not no_artwork,
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(bitrate),
            }
        ]
    }

    # Add EmbedThumbnail post-processor if artwork is enabled
    if not no_artwork:
        ydl_opts['postprocessors'].append({
            'key': 'EmbedThumbnail',
        })

    # Instantiate downloader
    ydl = yt_dlp.YoutubeDL(ydl_opts)

    # Add custom ID3 tagger post-processor at the end of the chain
    # Only pass playlist_title if it is actually a playlist
    tagger_album = playlist_title if is_playlist else None
    ydl.add_post_processor(ID3TaggerPostProcessor(playlist_title=tagger_album, clean_metadata=clean_metadata))

    log_info("Starting downloads...")
    try:
        ydl.download([url])
        log_success("Download and conversion process completed!")
    except Exception as e:
        log_error(f"An error occurred during download: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube Playlists, convert to MP3, and apply ID3 tags.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python3 downloader.py "https://www.youtube.com/playlist?list=PL..."
  python3 downloader.py "https://www.youtube.com/playlist?list=PL..." -b 320 -o ~/Music/MyPlaylist
  python3 downloader.py "https://www.youtube.com/watch?v=..." --no-artwork
        """
    )
    parser.add_argument("url", help="YouTube video or playlist URL")
    parser.add_argument("-b", "--bitrate", type=int, default=192, choices=[96, 128, 160, 192, 256, 320],
                        help="Target MP3 bitrate in kbps (default: 192)")
    parser.add_argument("-o", "--output", default="downloads",
                        help="Directory to save downloaded files (default: 'downloads')")
    parser.add_argument("--no-artwork", action="store_true",
                        help="Disable downloading and embedding video thumbnails as album artwork")
    parser.add_argument("--raw-metadata", action="store_true",
                        help="Disable title/artist auto-cleaning (keep raw YouTube video title and uploader)")
    parser.add_argument("--no-index", action="store_true",
                        help="Do not prefix filenames with playlist track numbers")

    args = parser.parse_args()

    print(f"\n{COLOR_HEADER}=========================================================={COLOR_RESET}")
    print(f"{COLOR_HEADER}   YouTube Playlist Downloader & MP3 Tagging Utility      {COLOR_RESET}")
    print(f"{COLOR_HEADER}=========================================================={COLOR_RESET}")
    print(f"{COLOR_BOLD}Destination Folder{COLOR_RESET}: {args.output}")
    print(f"{COLOR_BOLD}Target Bitrate{COLOR_RESET}    : {args.bitrate} kbps")
    print(f"{COLOR_BOLD}Embed Artwork{COLOR_RESET}     : {'No' if args.no_artwork else 'Yes'}")
    print(f"{COLOR_BOLD}Clean Metadata{COLOR_RESET}    : {'No' if args.raw_metadata else 'Yes'}")
    print(f"{COLOR_BOLD}Playlist Indexing{COLOR_RESET} : {'No' if args.no_index else 'Yes'}")
    print(f"{COLOR_HEADER}----------------------------------------------------------{COLOR_RESET}\n")

    download_playlist(
        url=args.url,
        bitrate=args.bitrate,
        output_dir=args.output,
        no_artwork=args.no_artwork,
        clean_metadata=not args.raw_metadata,
        no_playlist_indexing=args.no_index
    )

if __name__ == "__main__":
    main()
