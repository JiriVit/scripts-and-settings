"""
Splits a MP3 album to single songs.

Usage:
split_mp3_album.py album.mp3 tracklist.txt

  album.mp3      Path to .mp3 file with the album.
  tracklist.txt  Path to tracklist with track start times and titles.

Pre-requisites:
- ffmpeg binary + its location listed in PATH
- ffmpeg-python
- mutagen

Recommended YouTube to MP3 Converter:
y2mate.is

TODO Add writing of artist, album and cover art to the ID3 tag. This will require use of an input
     definition file (because command line doesn't support UTF-8 characters) and standard ID3 class
     (instead of EasyID3 which doesn't support cover art).
TODO Add autodetection of tracklist format ... or interactive selection.
TODO Smoothen the use of artist in the new format, there is room for improvement.
"""

import glob
import os
import re
import sys

import ffmpeg
from mutagen.easyid3 import EasyID3

# debug options
SKIP_EXISTING_TRACKS = False
STOP_AFTER_X_TRACKS = None



# matches "00:00:00   trackname"
TRACKLIST_REGEX1 = r"([\d:]+)\s+(.+)"
# matches "[00:00:00] trackname"
TRACKLIST_REGEX2 = r"\[([\d:]+)\]\s+(.+)"

TRACK_FORMATS = [
    # "00:00:00 title"
    (r"([\d:]+)\s+(.+)", ['start_time', 'title']),
    # "[00:00:00] title"
    (r"\[([\d:]+)\]\s+(.+)", ['start_time', 'title']),
    # "00.title [00:00:00]"
    (r"\d+\.(.+)\s+\[([\d:]+)\]", ['title', 'start_time']),
    # "[00:00:00] artist - title"
    (r"([\d:]+)\s+(.+)\s-\s(.+)", ['start_time', 'artist', 'title']),
]

# process command-line arguments
if len(sys.argv) == 3:
    album_mp3_path = sys.argv[1]
    tracklist_path = sys.argv[2]
else:
    mp3_list = glob.glob('*.mp3')
    if len(mp3_list) > 0:
        album_mp3_path = mp3_list[0]
        print('No MP3 file specified, using first found \'%s\'' % album_mp3_path)
    else:
        print('ERROR: No MP3 file specified, none found.')
        sys.exit(1)
    txt_list = glob.glob('*.txt')
    if len(txt_list) > 0:
        tracklist_path = txt_list[0]
        print('No tracklist specified, using first found \'%s\'' % tracklist_path)
    else:
        print('ERROR: No tracklist specified, none found.')
        sys.exit(1)

# 1. Parse the tracklist

# read lines from tracklist text file
with open(tracklist_path, "rt", encoding="utf8") as fobj:
    lines = fobj.readlines()

# parse the line with a regex, to get track info
track_format = TRACK_FORMATS[3]
track_regex = track_format[0]
track_fields = track_format[1]
regex = re.compile(track_regex)
tracklist = []
for line in lines:
    match = regex.match(line)
    track_info = {}
    for i in range(len(track_fields)):
        track_info[track_fields[i]] = match.group(i+1)
    tracklist.append(track_info)

# ask for confirmation of parsed tracklist
print("Tracklist was parsed to following items:")
for i, item in enumerate(tracklist):
    print(f"{i:02d} {item['start_time']} {item['title']}")
ans = input("Please confirm [Y/n]:")
if ans.lower() == 'n':
    sys.exit()



# 2. Split the album MP3 to single tracks

# load the album MP3
album_stream = ffmpeg.input(album_mp3_path).audio

# iterate through tracklist
track_count = len(tracklist)
for i, track_info in enumerate(tracklist):

    # get data fields from track info
    track_number = i + 1
    track_start = track_info["start_time"]
    if i < (track_count - 1):
        track_end = tracklist[i + 1]["start_time"]
    else:
        track_end = None
    track_title = track_info["title"]

    # TODO Use bitrate of the input file. We now set the bitrate explicitly, because it
    #      was reduced from original 160k to 128k, for some reason.

    # write output stream
    track_filename = f"{track_number:02d} {track_title}.mp3"
    track_path = track_filename
    if not (os.path.exists(track_path) and SKIP_EXISTING_TRACKS):
        if not track_end is None:
            track_stream = ffmpeg.output(album_stream, track_path, audio_bitrate="160k",
                ss=track_start, to=track_end)
        else:
            track_stream = ffmpeg.output(album_stream, track_path, audio_bitrate="160k",
                ss=track_start)
        ffmpeg.run(track_stream)

    # write ID3 tags
    id3 = EasyID3(track_path)
    id3["tracknumber"] = f"{track_number:02d}"
    id3["title"] = track_title
    if 'artist' in track_info:
        id3['artist'] = track_info['artist']
    id3.save()

    # stop after X tracks (to save time while debugging)
    if (STOP_AFTER_X_TRACKS is not None) and (i == (STOP_AFTER_X_TRACKS - 1)):
        break
