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


    def save(self):
        """Save ID3 tags to the MP3 file."""
        self.tags.save(v2_version=3)


    def __get_tag(self, tag_id):
        tag = None
        if tag_id in self.tags:
            tag = self.tags[tag_id].text[0]

        return tag


class AlbumInfo:
    """Encapsulates data of a MP3 album."""

    def __init__(self, path='.'):
        self.path = path
        
        files_list = os.listdir(path)
        mp3_list = [f for f in files_list if f.endswith('.mp3')]

        self.track_list = []
        for mp3_filename in mp3_list:
            self.track_list.append(TrackInfo(mp3_filename))


    def export_to_xml(self, actions=Action.NONE):
        """Export album information to a XML file.
        
        Args:
        actions: Actions to be performed before the export.
        """
        if actions & Action.PINYIN:
            pj = pinyin_jyutping.PinyinJyutping()

        album_element = ET.Element('album')
        for track_info in self.track_list:
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
    album_info = AlbumInfo()
    album_info.export_to_xml()
