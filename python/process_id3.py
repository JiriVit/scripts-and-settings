"""
process_id3.py: performs stuff with ID3 tags of MP3 files.

Usage: 
process_id3.py action 

Arguments:
action   Action to be performed. Supported values:
         - export: export ID3 tags to a XML file
         - import: import ID3 tags from a XML file
"""

import os
import sys
import xml.etree.cElementTree as ET
from enum import Flag

# 3rd party libraries
import pinyin_jyutping
from mutagen.id3 import Encoding, ID3, TALB, TDRC, TIT2, TPE1, TPE2, TRCK

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
        self.year = str(self.__get_tag('TDRC'))
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
            'year': self.year,
        }
        ET.SubElement(album_element, 'track', attrib=attrib)


    def import_xml_element(self, element):
        """Import ID3 from a XML element.

        Args:
        element: The XML element to import data from.
        """
        self.track_number = element.attrib.get('number')
        self.artist = element.attrib.get('artist')
        self.title = element.attrib.get('title')


    def save(self):
        """Save ID3 tags to the MP3 file."""
        self.__set_tag('TRCK', self.track_number)
        self.__set_tag('TIT2', self.title)
        self.__set_tag('TPE1', self.artist)
        self.__set_tag('TPE2', self.album_artist)
        self.__set_tag('TALB', self.album)
        self.__set_tag('TDRC', self.year)
        self.tags.save(v2_version=3)


    def __get_tag(self, tag_id):
        tag = None
        if tag_id in self.tags:
            tag = self.tags[tag_id].text[0]

        return tag


    def __set_tag(self, tag_id, value):
        if value is not None:
            if tag_id == 'TIT2':
                self.tags[tag_id] = TIT2(encoding=Encoding.UTF8, text=value)
            elif tag_id == 'TALB':
                self.tags[tag_id] = TALB(encoding=Encoding.UTF8, text=value)
            elif tag_id == 'TDRC':
                self.tags[tag_id] = TDRC(encoding=Encoding.UTF8, text=value)
            elif tag_id == 'TRCK':
                self.tags[tag_id] = TRCK(encoding=Encoding.UTF8, text=value)
            elif tag_id == 'TPE1':
                self.tags[tag_id] = TPE1(encoding=Encoding.UTF8, text=value)
            elif tag_id == 'TPE2':
                self.tags[tag_id] = TPE2(encoding=Encoding.UTF8, text=value)


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
        tree.write('album.xml', encoding='utf-8', xml_declaration=True)
        print('ID3 tags have been exported to file album.xml.')


    def import_from_xml(self):
        """Import data from a XML file and store to the ID3 tags of the MP3 files."""

        tree = ET.parse('album.xml')
        album_element = tree.getroot()
        
        number_of_elements = len(album_element)
        number_of_files = len(self.track_list)

        if number_of_elements == number_of_files:
            for i in range(number_of_elements):
                self.track_list[i].import_xml_element(album_element[i])
                self.track_list[i].save()
            print('ID3 tags have been imported from file album.xml.')
        else:
            print(f'ERROR: Count mismatch, there are {number_of_files} MP3 files and' + 
                  f' {number_of_elements} tracks in the XML file.')


#---------------------------------------------------------------------------------------------------
# Script Body
#---------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) > 1:
        album_info = AlbumInfo('.')
        if sys.argv[1] == 'export':
            album_info.export_to_xml()
        elif sys.argv[1] == 'import':
            album_info.import_from_xml()
    else:
        print(__doc__)
