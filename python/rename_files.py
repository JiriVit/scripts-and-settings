"""
Script of mass renaming of files, with support for UTF-8.

TODO Add verification of command line arguments.
"""

import glob
import os
import sys

# process input arguments
input_pattern = sys.argv[1]
input_source = sys.argv[2]

# get list of files matching the pattern
files_list = glob.glob(input_pattern)

# get list of new names from the source
with open(input_source, encoding='utf-8') as fobj:
    lines = [line.rstrip() for line in fobj]

# if the lists have same length, rename the files
if len(files_list) == len(lines):
    for src, dst in zip(files_list, lines):
        print('Renaming %s to %s' % (src, dst))
        os.rename(src, dst)
else:
    print('Number of files and new names don\'t match')
    sys.exit(1)