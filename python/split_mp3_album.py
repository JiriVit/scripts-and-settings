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
"""

#TODO Add fault isolation for tracklist parsing. Print the specific track which couldn't be parsed.

import glob
import os
import re
import sys
import xml.etree.cElementTree as ET

import ffmpeg
from mutagen.id3 import Encoding, PictureType, ID3, APIC, TALB, TDRC, TIT2, TPE1, TPE2, TRCK
from mutagen.mp3 import MP3

#---------------------------------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------------------------------

# debug options
SKIP_EXISTING_TRACKS = False
STOP_AFTER_X_TRACKS = None

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
        else:
            print('ERROR: No MP3 file specified, none found.')
            sys.exit(1)
        txt_list = glob.glob('*.txt')
        if len(txt_list) > 0:
            tracklist_path = txt_list[0]
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
    ans = int(input(f'\nSelect format (1-{trfl_len}): '))
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
    print('\nTracklist has been parsed to following items:')
    print('\n'.join([str(x) for x in tracklist]))
    ans = input('\nPlease confirm [Y/n]:')
    if ans.lower() == 'n':
        sys.exit(0)
    
    return tracklist


def create_album_xml(tracklist):
    """Create file 'album.xml' with list of tracks and their parsed information.
    
    Args:
    tracklist: Tracklist as a list of dicts.
    """

    album_attrib = {
        'name': '',
        'artist': '',
        'year': '',
        'cover': '',
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
        album_attrib['artist'] = tk0['artist']
    elif not no_artist:
        album_attrib['artist'] = 'VA'

    # detect a cover
    files = os.listdir('.')
    files = [f for f in files if f.endswith('.jpg')]
    if len(files) > 0:
        album_attrib['cover'] = files[0]

    # create XML tree
    album_element = ET.Element('album', attrib=album_attrib)
    for trk in tracklist:        
        attrib = {
            'start_time': trk['start_time']
        }
        if no_artist or same_artist:
            attrib['artist'] = '%album_artist%'
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
    print('\nTracklist has been converted to file album.xml.')
    print('Please review the file and run the script again to split the MP3.')


def split_mp3(mp3_path):
    """Split MP3 file to single tracks according to information stored in
    file 'album.xml'.

    Args:
    mp3_path: Path to the MP3 file.
    """

    # load album MP3
    album_stream = ffmpeg.input(mp3_path).audio

    # load album XML
    tree = ET.parse('album.xml')
    album_element = tree.getroot()
    
    # load cover image
    img = album_element.attrib['cover']
    if os.path.isfile(img):
        with open(img, 'rb') as fobj:
            img = fobj.read()
    else:
        img = None

    # get bitrate
    audio = MP3(mp3_path)
    bitrate = int(audio.info.bitrate / 1000)    

    # iterate through tracklist
    track_count = len(album_element)
    for i, track_element in enumerate(album_element):

        # get data fields from track info
        tnum = i + 1
        tsta = track_element.attrib['start_time']
        if i < (track_count - 1):
            tend = album_element[i + 1].attrib['start_time']
        else:
            tend = None
        ttit = track_element.attrib['title']
        tart = track_element.attrib['artist']

        # build filename
        if tart == '%album_artist%':
            tart = album_element.attrib['artist']
            fnart = ''
        else:
            fnart = f'{tart} - '

        # write output stream
        track_filename = f'{tnum:02d} {fnart}{ttit}.mp3'
        track_path = track_filename
        if not (os.path.exists(track_path) and SKIP_EXISTING_TRACKS):
            if not tend is None:
                track_stream = ffmpeg.output(album_stream, track_path, audio_bitrate=f'{bitrate}k',
                    ss=tsta, to=tend)
            else:
                track_stream = ffmpeg.output(album_stream, track_path, audio_bitrate=f'{bitrate}k',
                    ss=tsta)
            ffmpeg.run(track_stream)

        # write ID3 tags
        id3 = ID3(track_path)
        id3.delete()
        id3.add(TRCK(encoding=Encoding.UTF8, text=f'{tnum:02d}'))
        id3.add(TIT2(encoding=Encoding.UTF8, text=ttit))
        id3.add(TPE1(encoding=Encoding.UTF8, text=tart))
        id3.add(TPE2(encoding=Encoding.UTF8, text=album_element.attrib['artist']))
        id3.add(TALB(encoding=Encoding.UTF8, text=album_element.attrib['name']))
        id3.add(TDRC(encoding=Encoding.UTF8, text=album_element.attrib['year']))
        if img is not None:
            id3.add(APIC(mime='image/jpeg', type=PictureType.COVER_FRONT, data=img))
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
        split_mp3(al_path)

if __name__ == '__main__':
    main()
