# This is a sample Python script.
import os
url = "https://youtube.com/playlist?list=PLiN-7mukU_REPaZRXd62NKx1zoFXLnIRe" #@param {type:"string"}

# beginning and end of playlist items to download (Also: set download_full_playlist=False below)
playlist_start = '1'
playlist_end = '2'
download_full_playlist= True

quality = "192K"
playlist_album = "Blade Runner"
playlist_artist = "Vangelis"
title = playlist_album.replace(" ", "_")

download_videos = False
remove_everything = True 

os.system('pip install yt-dlp mutagen')

if remove_everything:
    os.system('rm -fr *.webm; rm -fr *.mp*')

#Download videos?:###############

if download_videos:
    if download_full_playlist:
        cmd = "yt-dlp " + url + " --format 18"
    else:
        cmd = "yt-dlp " + url + " --playlist-start {playlist_start} --playlist-end {playlist_end} --format 18"
else:
    if download_full_playlist:
        cmd = 'yt-dlp ' + url + ' --ignore-errors --format bestaudio --extract-audio --audio-format mp3 --audio-quality ' + quality + ' --output "%(playlist_index)s - %(title)s.%(ext)s" --yes-playlist'
    else:
        cmd = 'yt-dlp ' + url + ' --ignore-errors --format bestaudio --extract-audio --audio-format mp3 --audio-quality ' + quality + ' --output "%(playlist_index)s - %(title)s.%(ext)s" --playlist-start ' + playlist_start + ' --playlist-end ' + playlist_end + ' --yes-playlist'

print(cmd)
os.system(cmd)

# TAGGING MP3s ###################################

from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import mutagen.id3
from mutagen.id3 import ID3, TIT2, TIT3, TALB, TPE1, TRCK, TYER

import glob
import numpy as np


filez = glob.glob("*.mp3")

for i in np.arange(0, len (filez)):
	# extract the length of the directory
	length_directory = len(filez[i].split("/"))
	# extract the track number from the last element of the file path
	tracknum = filez[i].split("/")[length_directory-1][0:2]
	# mp3 name (with directory) from filez
	song = filez[i]
	# turn it into an mp3 object using the mutagen library
	mp3file = MP3(song, ID3=EasyID3)
	# set the album name
	mp3file['album'] = [playlist_album]
	# set the albumartist name
	mp3file['albumartist'] = [playlist_artist]
	# set the track number with the proper format
	mp3file['tracknumber'] = str(tracknum) + '/' + str(len(filez))
	# save the changes that we've made
	mp3file.save()

os.system('mkdir -p ' + title + '; mv *.mp* ' + title +'/')
