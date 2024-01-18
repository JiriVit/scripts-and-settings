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
y2mate.com

TODO Add use of XML definition file.
TODO Smoothen the use of artist in the new format, there is room for improvement.
"""

import glob
import os
import re
import sys
import xml.etree.cElementTree as ET

import ffmpeg
from mutagen.easyid3 import EasyID3

#---------------------------------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------------------------------

# debug options
SKIP_EXISTING_TRACKS = False
STOP_AFTER_X_TRACKS = 1

TRACK_FORMATS = [
    ('00:00 Title', r'([\d:]+)\s+(.+)', ['start_time', 'title']),
    ('[00:00] Title', r'\[([\d:]+)\]\s+(.+)', ['start_time', 'title']),
    ('00.Title [00:00]', r'\d+\.(.+)\s+\[([\d:]+)\]', ['title', 'start_time']),
    ('00:00 Artist - Title', r'([\d:]+)\s+(.+)\s-\s(.+)', ['start_time', 'artist', 'title']),
]

#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

def get_input_filenames():
    if len(sys.argv) == 3:
        album_mp3_path = sys.argv[1]
        tracklist_path = sys.argv[2]
    else:
        mp3_list = glob.glob('*.mp3')
        if len(mp3_list) > 0:
            album_mp3_path = mp3_list[0]
            print(f"WARNING: No MP3 file specified, using '{album_mp3_path}'.")
        else:
            print('ERROR: No MP3 file specified, none found.')
            sys.exit(1)
        txt_list = glob.glob('*.txt')
        if len(txt_list) > 0:
            tracklist_path = txt_list[0]
            print(f"WARNING: No tracklist specified, using '{tracklist_path}'")
        else:
            print('ERROR: No tracklist specified, none found.')
            sys.exit(1)
    
    return (album_mp3_path, tracklist_path)


def parse_tracklist(path):

    # read lines from tracklist text file
    with open(path, "rt", encoding="utf8") as fobj:
        lines = fobj.readlines()

    # ask for selection of tracklist format
    print(f'\nFirst line of provided tracklist:')
    print(lines[0])
    print('Supported tracklist formats:')
    trfl_len = len(TRACK_FORMATS)
    for i in range(trfl_len):
        trf = TRACK_FORMATS[i]
        print(f'{i + 1}:   {trf[0]}')
    ans = int(input('Select format (1-4): '))
    selected_trf = TRACK_FORMATS[int(ans) - 1]

    # parse the line with a regex, to get track info
    trf_regex = selected_trf[1]
    trf_fields = selected_trf[2]
    regex = re.compile(trf_regex)
    tracklist = []
    for line in lines:
        match = regex.match(line)
        track_info = {}
        for i in range(len(trf_fields)):
            track_info[trf_fields[i]] = match.group(i+1)
        tracklist.append(track_info)

    # ask for confirmation of parsed tracklist
    print("Tracklist has been parsed to following items:")
    print('\n'.join([str(x) for x in tracklist]))
    ans = input("Please confirm [Y/n]:")
    if ans.lower() == 'n':
        sys.exit(0)
    
    return tracklist


def create_album_xml(tracklist):
    album_attrib = {
        'name': '',
        'artist': '',
        'year': '',
        'album_artist': '',
    }

    # find out if all track have same artist or no artist
    tk0 = tracklist[0]
    no_artist = True
    same_artist = True
    for trk in tracklist:
        if 'artist' in tk0:
            no_artist = False
            if 'artist' in trk:
                if tk0['artist'] != trk['artist']:
                    same_artist = False
                    break
            else:
                same_artist = False
                break

    if same_artist:
        album_attrib.pop('artist')
        album_attrib['album_artist'] = tk0['artist']

    # create XML tree
    album_element = ET.Element('album', attrib=album_attrib)
    for trk in tracklist:        
        attrib = {
            'start_time': trk['start_time']
        }
        if no_artist:
            attrib['artist'] = '%album%'
        elif 'artist' in trk:
            attrib['artist'] = trk['artist']
        else:
            attrib['artist'] = ''
        attrib['title'] = trk['title']
        ET.SubElement(album_element, 'track', attrib=attrib)
    tree = ET.ElementTree(album_element)
    ET.indent(tree)

    # write the XML tree to a file
    tree.write('album.xml', encoding='utf-8', xml_declaration=True)


def split_album(mp3_path):

    # load album MP3
    album_stream = ffmpeg.input(mp3_path).audio

    # load album XML
    tree = ET.parse('album.xml')
    album_element = tree.getroot()

    # iterate through tracklist
    track_count = len(album_element)
    for i, track_element in enumerate(album_element):

        # get data fields from track info
        track_number = i + 1
        track_start = track_element.attrib['start_time']
        if i < (track_count - 1):
            track_end = album_element[i + 1].attrib['start_time']
        else:
            track_end = None
        track_title = track_element.attrib['title']

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
        if 'artist' in track_element.attrib:
            id3['artist'] = track_element.attrib['artist']
        id3.save()

        # stop after X tracks (to save time while debugging)
        if (STOP_AFTER_X_TRACKS is not None) and (i == (STOP_AFTER_X_TRACKS - 1)):
            break

#---------------------------------------------------------------------------------------------------
# Script Body
#---------------------------------------------------------------------------------------------------

def main():
    (al_path, tl_path) = get_input_filenames()
    if not os.path.isfile('album.xml'):
        tracklist = parse_tracklist(tl_path)
        create_album_xml(tracklist)
    else:
        split_album(al_path)

if __name__ == '__main__':
    main()
