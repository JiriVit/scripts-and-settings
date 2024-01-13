"""
process_id3.py: performs stuff with ID3 tags of MP3 files.

Usage: 
process_id3.py action [options]

Arguments:
action   Action to be performed. Supported values:
         - export: export ID3 tags to a XML file
         - import: import ID3 tags from a XML file
         - rename: rename the files per their ID3 tags
options  Options for the action. Supported values:
         - pinyin: convert chinese track titles to pinyin before export
         - album: treat the files as an album with a single artist
         - compilation: treat the files as an compilation with multiple artists
"""

# TODO Add support for jyutping.
# TODO Add support for romaji.
# TODO Add support for transcription of album and artist names.
# TODO Add support for choice between album and compilation.
# TODO Add restriction for transcription only if the whole string is in that language.
# TODO Add auto detection of language.

import os
import sys
import xml.etree.cElementTree as ET
from enum import Flag

# 3rd party libraries
from pinyin_jyutping import PinyinJyutping
from mutagen.id3 import Encoding, PictureType, ID3, APIC, TALB, TDRC, TIT2, TPE1, TPE2, TRCK

#---------------------------------------------------------------------------------------------------
# Constants
#---------------------------------------------------------------------------------------------------

ROMANIZATION_DICT = {
    '鳳飛飛': 'Fong Fei-Fei',
}

#---------------------------------------------------------------------------------------------------
# Classes
#---------------------------------------------------------------------------------------------------


class Options(Flag):
    """Enumerates supported options."""
    
    NONE = 0x00
    """No options."""

    PINYIN = 0x01
    """Adds pinyin for track and album titles in Chinese."""

    JYUTPING = 0x02
    """Adds jyutping for track and album titles in Cantonese."""

    ROMAJI = 0x04
    """Adds romaji for track and album titles in Japanese."""

    ALBUM = 0x10
    """Treats the album as album with one common artist."""

    COMPILATION = 0x20
    """Treats the album as compilation with multiple artists."""


class TrackInfo:
    """Encapsulates ID3 tags of a MP3 file and provides methods to work with them."""

    pj = None

    def __init__(self, path):
        self.path = path
        self.tags = ID3(path)
        self.track_number = self.__get_tag('TRCK')
        self.title = self.__get_tag('TIT2')
        self.artist = self.__get_tag('TPE1')
        self.album = self.__get_tag('TALB')
        self.year = str(self.__get_tag('TDRC'))
        self.album_artist = self.__get_tag('TPE2')


    def create_xml_element(self, album_element, export_artist=False, export_year=False):
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
        if not export_artist:
            attrib.pop('artist')
        if not export_year:
            attrib.pop('year')

        ET.SubElement(album_element, 'track', attrib=attrib)


    def import_xml_element(self, element:ET.Element):
        """Import ID3 from a XML element.

        Args:
        element: The XML element to import data from.
        """
        self.track_number = element.attrib.get('number')
        self.artist = element.attrib.get('artist')
        self.title = element.attrib.get('title')


    def import_front_cover(self, path):
        """Imports front cover from a JPG file and stores it to ID3 tag.

        Args:
        path: Path to the JPG file.
        """

        with open(path, 'rb') as fobj:
            pict_data = fobj.read()

        pict = APIC(mime='image/jpeg', type=PictureType.COVER_FRONT, data=pict_data)
        self.tags.delall('APIC')
        self.tags.add(pict)


    def save(self):
        """Save ID3 tags to the MP3 file."""
        self.__set_tag('TRCK', self.track_number)
        self.__set_tag('TIT2', self.title)
        self.__set_tag('TPE1', self.artist)
        self.__set_tag('TPE2', self.album_artist)
        self.__set_tag('TALB', self.album)
        self.__set_tag('TDRC', self.year)
        self.tags.save(v2_version=3)


    def rename(self, options):
        """Rename the MP3 file per info in its ID3 tags.
        
        Args:
        options: Options for the operation.
        """
        new_path = None
        if options & Options.ALBUM:
            new_path = f'{self.track_number} {self.title}.mp3'
        elif options & Options.COMPILATION:
            new_path = f'{self.track_number} {self.artist} - {self.title}.mp3'
        
        if new_path is not None:
            os.rename(self.path, new_path)


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

    pj = None

    def __init__(self, path='.', options=Options.NONE):
        self.path = path
        self.options = options
        
        files_list = os.listdir(path)
        mp3_list = [f for f in files_list if f.endswith('.mp3')]

        self.track_list = []
        for mp3_filename in mp3_list:
            self.track_list.append(TrackInfo(mp3_filename))


    def export_to_xml(self):
        """Export album information to a XML file.
        
        Args:
        options: Options for the export.
        """

        self.__build_album_attrib()
        album_element = ET.Element('album', attrib=self.album_attrib)
        for track_info in self.track_list:
            track_info.title = self.__add_romanization(track_info.title)
            track_info.create_xml_element(album_element, 
                                          export_artist = not self.same_artist, 
                                          export_year = not self.same_year)

        tree = ET.ElementTree(album_element)
        ET.indent(tree)
        tree.write('album.xml', encoding='utf-8', xml_declaration=True)
        print('ID3 tags have been exported to file album.xml.')


    def import_from_xml(self):
        """Import data from a XML file and store to the ID3 tags of the MP3 files."""

        # load the XML file
        tree = ET.parse('album.xml')
        self.album_element = tree.getroot()

        # get cover image (if there is exactly one JPG file in the folder)
        files = os.listdir()
        jpg_files = [f for f in files if f.endswith('.jpg')]
        if len(jpg_files) == 1:
            self.cover_path = jpg_files[0]
        else:
            self.cover_path = None

        number_of_elements = len(self.album_element)
        number_of_files = len(self.track_list)

        if number_of_elements == number_of_files:
            for i in range(number_of_elements):
                self.__import_track_element(i)
            print('ID3 tags have been imported from file album.xml.')
        else:
            print(f'ERROR: Count mismatch, there are {number_of_files} MP3 files and' + 
                  f' {number_of_elements} tracks in the XML file.')


    def rename_files(self):
        """Renames the MP3 files per their ID3 tags."""

        if self.options & (Options.ALBUM | Options.COMPILATION):
            for track_info in self.track_list:
                track_info.rename(self.options)
        else:
            print("ERROR: Missing option 'album' / 'compilation'.")
            print(__doc__)


    def __build_album_attrib(self):
        """Build dict of attribs for album XML element and store it to instance variable 
        self.album_attrib.
        """

        # these indicate if all tracks have the same artist and year
        self.same_artist = True
        self.same_year = True
        track_count = len(self.track_list)
        if track_count > 1:
            for i in range(1, track_count):
                if not self.track_list[0].artist == self.track_list[i].artist:
                    self.same_artist = False
                if not self.track_list[0].year == self.track_list[i].year:
                    self.same_year = False

        # create aliases for shorter code
        tk0 = self.track_list[0]
        aat = dict()

        # determine album XML element attribs 
        if tk0.album is not None:
            aat['name'] = self.__add_romanization(tk0.album)
        else:
            aat['name'] = ''
        if self.same_artist:
            if tk0.artist is not None:
                aat['artist'] = \
                    self.__add_romanization(tk0.artist, preserve_original=False, lookup=True)
            else:
                aat['artist'] = ''
        if self.same_year:
            if tk0.year is not None:
                aat['year'] = tk0.year
            else:
                aat['year'] = ''
        if tk0.album_artist is not None:
            aat['album_artist'] = \
                self.__add_romanization(tk0.album_artist, preserve_original=False, lookup=True)
        else:
            aat['album_artist'] = '' 

        # store the attribs from local alias to instance variable
        self.album_attrib = aat


    def __import_track_element(self, index):
        """Import data from track XML element to track ID3 tags, then add necessary data
        from album XML element.
        """

        # create aliases
        tel = self.album_element[index]
        aat = self.album_element.attrib
        trk = self.track_list[index]

        # import from track element to the ID3 tags
        trk.import_xml_element(tel)

        # import from album element to the ID3 tags
        if 'name' in aat:
            trk.album = aat['name']
        if 'album_artist' in aat:
            trk.album_artist = aat['album_artist']
        if 'front_cover' in aat:
            trk.import_front_cover(aat['front_cover'])
        elif self.cover_path is not None:
            trk.import_front_cover(self.cover_path)

        # replace track artist with album artist, if needed
        if ((not 'artist' in tel.attrib) or (tel.attrib['artist'] is None)) and \
           ('artist' in aat):
            trk.artist = aat['artist'] 
        
        # replace track year with album year, if needed
        if ((not 'year' in tel.attrib) or (tel.attrib['year'] is None)) and \
           ('year' in aat):
            trk.year = aat['year'] 
        
        # save ID3 tags to the MP3 file
        trk.save()


    def __add_romanization(self, text, preserve_original=True, lookup=False):

        romanization = text

        if lookup and (text in ROMANIZATION_DICT):
            romanization = ROMANIZATION_DICT[text]
        elif self.options & (Options.PINYIN | Options.JYUTPING):

            # this instance is quite expensive, so we create it once and reuse it
            if AlbumInfo.pj is None:
                AlbumInfo.pj = PinyinJyutping()

            try:
                if self.options & Options.PINYIN:
                    romanization = AlbumInfo.pj.pinyin(text, tone_numbers=True)
                else:
                    romanization = AlbumInfo.pj.jyutping(text, tone_numbers=True)
                romanization = [x for x in romanization if not x.isdigit()]
                romanization = ''.join(romanization).capitalize()
            except:
                print(f'ERROR: Romanization failed for string \'{text}\'')


        if preserve_original and (romanization != text):
            romanization = f'{romanization} ({text})'

        return romanization


#---------------------------------------------------------------------------------------------------
# Functions
#---------------------------------------------------------------------------------------------------


def debug():
    tags = ID3('sample.mp3')
    tags.delall('APIC')
    print(tags.pprint() + '\n')

    with open('cover1.jpg', 'rb') as fobj:
        pict_data = fobj.read()

    pict1 = APIC(mime='image/jpeg', type=PictureType.COVER_FRONT, data=pict_data, desc='1')
    tags.add(pict1)
    print(tags.pprint() + '\n')

    with open('cover2.jpg', 'rb') as fobj:
        pict_data = fobj.read()

    pict2 = APIC(mime='image/jpeg', type=PictureType.COVER_BACK, data=pict_data, desc='2')
    tags.add(pict2)
    print(tags.pprint() + '\n')

    print(tags.keys())

    tags.save()


def main():
    if len(sys.argv) > 1:
        action = sys.argv[1]

        # parse options
        options = Options.NONE
        if len(sys.argv) > 2:
            supported_options = {
                'pinyin': Options.PINYIN,
                'jyutping': Options.JYUTPING,
                'album': Options.ALBUM,
                'compilation': Options.COMPILATION
            }

            for i in range(2, len(sys.argv)):
                opt = sys.argv[i]
                if opt in supported_options:
                    options = options | supported_options[opt]
        
        album_info = AlbumInfo('.', options)
        
        supported_actions = {
            'export': album_info.export_to_xml,
            'import': album_info.import_from_xml,
            'rename': album_info.rename_files,
            'debug': debug
        }

        # perform the action
        if action in supported_actions:
            supported_actions[action]()
        else:
            print('ERROR: Action not supported')
            print(__doc__)
    else:
        print(__doc__)


#---------------------------------------------------------------------------------------------------
# Script Body
#---------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    main()
