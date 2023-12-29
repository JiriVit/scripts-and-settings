"""
Provides means for mass processing of ID3 tags of MP3 files.
"""

import os
import xml.etree.cElementTree as ET
from enum import Flag

# 3rd party libraries
import pinyin_jyutping
from mutagen.id3 import ID3, TPE1, Encoding

# Tag IDs used by MP3Tag and WinAmp:
# TALB = Album
# TPE1 = Artist
# TPE2 = Album Artist
# TIT2 = Title
# TRCK = Track
# TDRC = Year
# APIC: = Picture

#---------------------------------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------------------------------

PATH_TO_MP3 = "data/sample.mp3"

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------

class Action(Flag):
    """Enumerates supported actions."""
    
    NONE = 0x00
    """No action."""

    PINYIN = 0x01
    """Adds pinyin for track titles."""


class TrackInfo:
    """Encapsulates ID3 tags of a MP3 file and provides methods to work with them."""

    pj = None

    def __init__(self, path):
        self.tags = ID3(path)
        self.track_number = self.__get_tag('TRCK')
        self.title = self.__get_tag('TIT2')
        self.artist = self.__get_tag('TPE1')
        self.album = self.__get_tag('TALB')
        self.year = self.__get_tag('TDRC')
        self.album_artist = self.__get_tag('TPE2')


    def add_pinyin(self):
        if TrackInfo.pj is None:
            TrackInfo.pj = pinyin_jyutping.PinyinJyutping()

        pinyin = TrackInfo.pj.pinyin(self.title, tone_numbers=True)
        pinyin_removed_numbers = [x for x in pinyin if not x.isdigit()]
        pinyin_removed_numbers = ''.join(pinyin_removed_numbers).capitalize()
        self.title = f'{pinyin_removed_numbers} ({self.title})'


    def create_xml_element(self, album_element):
        """Create a XML element for the track.
        
        Args:
        album_element: Parent XML element of the album.
        """
        attrib = {
            'number': self.track_number,
            'artist': self.artist,
            'title': self.title,
        }
        ET.SubElement(album_element, 'track', attrib=attrib)


    def __get_tag(self, tag_id):
        tag = None
        if tag_id in self.tags:
            tag = self.tags[tag_id].text[0]

        return tag


#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------

def sample_id3_processing(path):

    # extract ID3 tags from the MP3 file 
    tags = ID3(path)

    # extract the tag with the artist (class mutagen.id3.TPE1)
    artist_tag = tags['TPE1']

    # extract the string from the tag
    artist_str = artist_tag.text[0]

    # write another string
    tags['TPE1'] = TPE1(encoding=Encoding.UTF8, text='Another artist')
    
    # save changes in the tags
    tags.save(v2_version=3)

    pict = tags['APIC:'].data

    with open('test.jpg', 'wb') as fobj:
        fobj.write(pict)


def get_list_of_mp3(path='.'):
    """Get list of MP3 files in given directory.

    Args:
    path: Path of the directory to get the files from.
    """
    files_list = os.listdir(path)
    mp3_list = [f for f in files_list if f.endswith('.mp3')]

    return mp3_list


def export_to_xml(actions=Action.NONE):
    """Exports ID3 tags from all MP3 files in current working directory to an XML file.

    Args:
    actions: Actions to be performed with the tags before exporting.
    """

    if actions & Action.PINYIN:
        pj = pinyin_jyutping.PinyinJyutping()

    mp3_list = get_list_of_mp3()
    album_element = ET.Element('album')
    for mp3_filename in mp3_list:
        track_info = TrackInfo(mp3_filename)
        if actions & Action.PINYIN:
            track_info.add_pinyin()
        track_info.create_xml_element(album_element)

    tree = ET.ElementTree(album_element)
    ET.indent(tree)
    tree.write('export.xml', encoding='utf8')


#---------------------------------------------------------------------------------------------------
# Script Body
#---------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    export_to_xml()
