#!/usr/bin/python3

#imports
import mmap
import sys
import os
from hashlib import file_digest

# globals
PREFIX = 'ExtractedFiles/'

class File:

    def __init__(s, prefix, extension, source):
        
        s.prefix = prefix
        s.ext = extension
        s.source = source

        s.filename = ''
        s.start = 0
        s.end = 0
        s.hash = 0

    def extract(s):

        fulldir = s.prefix + s.filename + '.' + s.ext

        with open(s.source, 'r+b') as f:
            mm = mmap.mmap(f.fileno(), 0)

            with open(fulldir, 'wb') as output: 
                output.write(mm[s.start:s.end])

        # get hash
        with open(fulldir, 'rb', buffering=0) as f:
            s.hash = file_digest(f, 'sha256').hexdigest()

    def print_info(s):

        print(f'{s.filename}.{s.ext}: Starts at: {s.start}, Ends at {s.end} (bytes)')
        print(f'SHA256 Hash: {s.hash}')

# main
def main():
    
    if len(sys.argv) != 2:
        print('Usage: ./extractor.py [INPUT FILE]')
        exit()

    source = sys.argv[1]

    # test file
    try:
        f = open(source, 'rb')
        f.close()
    except:
        print('Unable to open file (correct name?)')
        exit()

    files = []
    # find all instances of files
    files = find_MPG(source, files)

    # extract all instances of files

    if not os.path.exists(PREFIX):
        os.mkdir(PREFIX)

    for i, file in enumerate(files):
        file.filename = f'File{i}'
        file.extract()
        file.print_info()

# Finds all MPG files
def find_MPG(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = mm.find(b'\x00\x00\x01\xB3', offset)

        while header != -1:

            # verify header
            # byte 7 cannot be 00 or start with 5+ (see mpg sequence header info)
            byte7 = mm[header+7:header+8]
            b7v = int.from_bytes(byte7)
            
            if b7v < 0x11 or b7v > 0x48:
                offset = header + 4
                header = mm.find(b'\x00\x00\x01\xB3', offset)
                continue

            # footer
            footer = mm.find(b'\x00\x00\x01\xB7', header)

            if footer == -1:
                print(f'MPG file header at {header} has no associated footer')
                return list

            # sanity check
            #another = mm.find(b'\x00\x00\x01\xB3', header + 4, footer)

            #if another != -1:
            #    print(f'MPG file footer at {footer} has multiple possible headers, currently at {header}. Continuing search...')
            #    offset = header + 4
            #    header = mm.find(b'\x00\x00\x01\xB3', offset)
            #    continue
            
            print(f'MPG file found at {header}, {footer}')

            mpg_file = File(PREFIX, 'mpg', source)
            mpg_file.start = header
            mpg_file.end = footer + 4

            list.append(mpg_file)

            offset = footer + 4
            # head
            header = mm.find(b'\x00\x00\x01\xB3', offset)

    return list




    

# start
if __name__ == '__main__':
    main()