"""
Provides means for mass processing of ID3 tags of MP3 files.
"""

import os
import xml.etree.cElementTree as ET
from enum import Flag

# 3rd party libraries
import pinyin_jyutping
from mutagen.id3 import ID3, TPE1, Encoding

PATH_TO_MP3 = "data/sample.mp3"

class Action(Flag):
    """Enumerates supported actions."""
    
    NONE = 0x00
    """No action."""

    PINYIN = 0x01
    """Adds pinyin for track titles."""


# Tag IDs used by MP3Tag and WinAmp:
# TALB = Album
# TPE1 = Artist
# TPE2 = Album Artist
# TIT2 = Title
# TRCK = Track
# TDRC = Year
# APIC: = Picture


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


def get_list_of_mp3():
    files_list = os.listdir()
    mp3_list = [f for f in files_list if f.endswith('.mp3')]

    return mp3_list


def get_tag(path, tag_id):
    tags = ID3(path)
    tag_text = tags[tag_id].text[0]

    return tag_text


def export_to_xml(actions=Action.NONE):
    """Exports ID3 tags from all MP3 files in current working directory to an XML file.

    Args:
    actions: Actions to be performed with the tags before exporting.
    """

    if actions & Action.PINYIN:
        pj = pinyin_jyutping.PinyinJyutping()

    mp3_list = get_list_of_mp3()
    root = ET.Element('album')
    for mp3_filename in mp3_list:
        title = get_tag(mp3_filename, 'TIT2')
        if actions & Action.PINYIN:
            pinyin = pj.pinyin(title, tone_numbers=True)
            pinyin_removed_numbers = [x for x in pinyin if not x.isdigit()]
            pinyin_removed_numbers = ''.join(pinyin_removed_numbers).capitalize()
            corrected_title = f'{pinyin_removed_numbers} ({title})'
        else:
            corrected_title = title
        
        ET.SubElement(root, 'track', title=corrected_title)

    tree = ET.ElementTree(root)
    ET.indent(tree)
    tree.write('test.xml', encoding='utf8')


# SCRIPT BODY --------------------------------------------------------------------------------------

if __name__ == '__main__':
    export_to_xml()
