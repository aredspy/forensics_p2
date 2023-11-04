#!/usr/bin/

# Developed on Python 3.11

#imports
import mmap
import sys
import os
import hashlib
import struct
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
    find_MPG(source, files)
    find_DOCX(source, files)
    find_GIF(source, files)
    find_PDF(source, files)
    find_AVI(source, files)
    find_PNG(source, files)
    find_JPG(source, files)
    find_BMP(source, files)
    find_ZIP(source, files)

    # extract all instances of files

    if not os.path.exists(PREFIX):
        os.mkdir(PREFIX)

    for i, file in enumerate(files):
        file.filename = f'File{i}'
        file.extract()
        file.print_info()

# # Finds all MPG files
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
            
            print(f'MPG file found at {header}, {footer}')

            mpg_file = File(PREFIX, 'mpg', source)
            mpg_file.start = header
            mpg_file.end = footer + 4

            list.append(mpg_file)

            offset = footer + 4
            # head
            header = mm.find(b'\x00\x00\x01\xB3', offset)

    return list

# Finds all PDF files
def find_PDF(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        footer = 0

        # keeps up with beginnings and possible endings of PDF files
        header_offsets = []
        footer_offsets = []

        while header != -1:
            header = mm.find(b'\x25\x50\x44\x46', offset)

            #only add header to list if byte sequence is found
            if header != -1:
                header_offsets.append(header)
                offset = header + 4
        
        offset = 0
        while footer != -1:
            footer = mm.find(b'\x0A\x25\x25\x45\x4F\x46', offset)

            #only add footer to list of byte sequence is found
            if footer != -1:
                footer_offsets.append([footer, 6]) # 6 is the length of the footer
                offset = footer + 6

        offset = 0
        footer = 0
        while footer != -1:
            footer = mm.find(b'\x0A\x25\x25\x45\x4F\x46\x0A', offset)

            #only add footer to list of byte sequence is found
            if footer != -1:
                footer_offsets.append([footer, 7]) # 7 is the length of the footer
                offset = footer + 7

        offset = 0
        footer = 0
        while footer != -1:
            footer = mm.find(b'\x0D\x0A\x25\x25\x45\x4F\x46\x0D\x0A', offset)

            #only add footer to list of byte sequence is found
            if footer != -1:
                footer_offsets.append([footer, 9]) # 9 is the length of the footer
                offset = footer + 9

        offset = 0
        footer = 0
        while footer != -1:
            footer = mm.find(b'\x0D\x25\x25\x45\x4F\x46\x0D', offset)

            #only add footer to list of byte sequence is found
            if footer != -1:
                footer_offsets.append([footer, 7]) # 7 is the length of the footer
                offset = footer + 7
        
        # sort footers because they're not necessarily in the correct order
        footer_offsets.sort(key=lambda x: x[0])

        # this is supposed to make sure we use the last footer that occurs before the next header
        last_valid_footer_offset = None
        footer_length = None
        for i in range(len(header_offsets)):
            for j in range(len(footer_offsets)):
                if footer_offsets[j][0] > header_offsets[i]: #footer must come after the header
                    try:
                        if footer_offsets[j][0] < header_offsets[i+1]: #footer must come before the next header
                            last_valid_footer_offset = footer_offsets[j][0]
                            footer_length = footer_offsets[j][1]
                    except IndexError:
                        last_valid_footer_offset = footer_offsets[j][0]
                        footer_length = footer_offsets[j][1]
            
            print(f'PDF file found at {header_offsets[i]}, {last_valid_footer_offset}')

            pdf_file = File(PREFIX, 'pdf', source)
            pdf_file.start = header_offsets[i]
            pdf_file.end = last_valid_footer_offset + footer_length

            list.append(pdf_file)
        
    return list

# Finds all GIF files
def find_GIF(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        footer = 0

        # keeps up with beginnings and possible endings of GIF files
        header_offsets = []
        footer_offsets = []

        while header != -1:
            header = mm.find(b'\x47\x49\x46\x38\x37\x61', offset)

            #only add header to list if byte sequence is found
            if header != -1:
                header_offsets.append(header)
                offset = header + 6
        
        offset = 0
        header = 0
        while header != -1:
            header = mm.find(b'\x47\x49\x46\x38\x39\x61', offset)

            #only add header to list if byte sequence is found
            if header != -1:
                header_offsets.append(header)
                offset = header + 6
        
        #starting from each header, find the footer
        for i in range(len(header_offsets)):
            offset = header_offsets[i]
            footer = mm.find(b'\x00\x00\x3B', offset)

            if footer == -1:
                print(f'GIF file header at {header_offsets[i]} has no associated footer')
            
            footer_offsets.append(footer)

        #print(footer_offsets)

        # sanity check, hopefully this condition is never met
        if len(header_offsets) != len(footer_offsets):
            print("Error: Different number of header and footer offsets found for GIF files.")

        #create file object for GIF file
        for i in range(len(header_offsets)):
            print(f'GIF file found at {header_offsets[i]}, {footer_offsets[i]}')

            gif_file = File(PREFIX, 'gif', source)
            gif_file.start = header_offsets[i]
            gif_file.end = footer_offsets[i] + 3

            list.append(gif_file)
        
    return list

# Finds all DOCX files
def find_DOCX(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        footer = 0

        while header != -1:

            header = mm.find(b'\x50\x4B\x03\x04\x14\x00\x06\x00', offset)

            #only look for footer if header is valid
            if header != -1:

                # check for [Content_Types].xml subheader
                f.seek(header + 30)

                if f.read(19) != b'\x5b\x43\x6f\x6e\x74\x65\x6e\x74\x5f\x54\x79\x70\x65\x73\x5d\x2e\x78\x6d\x6c':
                    offset = header + 8
                    continue

                offset = header + 8 # skip 8 bytes of header

                footer = mm.find(b'\x50\x4B\x05\x06', offset)

                # this condition shouldn't be met
                if footer == -1:
                    print(f'MPG file header at {header} has no associated footer')
                    return list
                
                print(f'DOCX file found at {header}, {footer}')

                docx_file = File(PREFIX, 'docx', source)
                docx_file.start = header
                docx_file.end = footer + 22 # 4 bytes in the footer and 18 additional bytes after it

                list.append(docx_file)

                offset = footer + 4
        
    return list

# Finds all AVI files
def find_AVI(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        second_header_part = 0
        footer = 0

        while header != -1:
            header = mm.find(b'\x52\x49\x46\x46', offset) #look for first part of signature
            second_header_part = mm.find(b'\x41\x56\x49\x20\x4C\x49\x53\x54', offset) #look for second part of signature

            #only look for footer if header is valid
            if header != -1 and second_header_part - header == 8: 
                f.seek(header + 4) # this is where the file length is stored
                little_endian_bytes = f.read(4) 
                footer = header + struct.unpack('<I', little_endian_bytes)[0] + 8 # calculate where the footer is

                print(f'AVI file found at {header}, {footer}')

                avi_file = File(PREFIX, 'avi', source)
                avi_file.start = header
                avi_file.end = footer 

                list.append(avi_file)

                offset = footer # where to begin looking for next header
        
    return list

# Finds all PNG files
def find_PNG(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        footer = 0

        # keeps up with beginnings and endings of PNG files
        header_offsets = []
        footer_offsets = []

        while header != -1:
            header = mm.find(b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A', offset)

            #only add header to list if byte sequence is found
            if header != -1:
                header_offsets.append(header)
                offset = header + 8

        #starting from each header, find the footer
        for i in range(len(header_offsets)):
            offset = header_offsets[i]
            footer = mm.find(b'\x49\x45\x4E\x44\xAE\x42\x60\x82', offset)

            if footer == -1:
                print(f'PNG file header at {header_offsets[i]} has no associated footer')
            
            footer_offsets.append(footer)
        #create file object for PNG file
        for i in range(len(header_offsets)):
            print(f'PNG file found at {header_offsets[i]}, {footer_offsets[i]}')

            png_file = File(PREFIX, 'png', source)
            png_file.start = header_offsets[i]
            png_file.end = footer_offsets[i] + 8

            list.append(png_file)
        
    return list

# Finds all BMP files
def find_BMP(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        footer = 0

        while header != -1:
            header = mm.find(b'\x42\x4D', offset)

            #only add header to list if byte sequence is found and size matches footer
            if header != -1:

                f.seek(header + 2) # this is where the file length is stored
                little_endian_bytes = f.read(4) 
                footer = header + struct.unpack('<I', little_endian_bytes)[0] # calculate where the footer ends

                f.seek(header + 6)
                
                #check if header is valid
                if f.read(4) != b'\x00\x00\x00\x00':
                    offset = header + 2
                    continue

                print(f'BMP file found at {header}, {footer}')

                bmp_file = File(PREFIX, 'bmp', source)
                bmp_file.start = header
                bmp_file.end = footer 

                list.append(bmp_file)

                offset = footer # where to begin looking for next header

    return list

# Finds all JPG files
def find_JPG(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        footer = 0

        # keeps up with beginnings and endings of JPG files
        header_offsets = []
        footer_offsets = []

        while header != -1:

            header = mm.find(b'\xFF\xD8\xFF\xE0', offset)

            #only add header to list if byte sequence is found
            if header != -1:
                header_offsets.append(header)
                offset = header + 4

        # special exif format header
        header = 0
        offset = 0
        while header != -1:

            header = mm.find(b'\xff\xd8\xff\xdb', offset)

            #only add header to list if byte sequence is found
            if header != -1:
                header_offsets.append(header)
                offset = header + 4

            #starting from each header, find the footer
        for i in range(len(header_offsets)):
            offset = header_offsets[i]
            footer = mm.find(b'\xFF\xD9', offset)

            if footer == -1:
                print(f'JPG file header at {header_offsets[i]} has no associated footer')
            
            footer_offsets.append(footer)

        for i in range(len(header_offsets)):
            print(f'JPG file found at {header_offsets[i]}, {footer_offsets[i]}')

            jpg_file = File(PREFIX, 'jpg', source)
            jpg_file.start = header_offsets[i]
            jpg_file.end = footer_offsets[i] + 2

            list.append(jpg_file)

    return list

# Finds all ZIP files  
def find_ZIP(source, list):

    with open(source, 'r+b') as f:
        mm = mmap.mmap(f.fileno(), 0)
        offset = 0
        header = 0
        footer = 0

        # keeps up with beginnings and endings of ZIP files
        header_offsets_temp = []
        header_offsets_final = []
        compressed_file_sizes = []
        filename_length_list = []
        filenames = []
        footer_offsets = []
        files = []
        final_files = []

        while header != -1:

            header = mm.find(b'\x50\x4B\x03\x04', offset)
            
            #only add header to list if byte sequence is found
            if header != -1:
                f.seek(header)
                full_header_seven = f.read(7)
                f.seek(header)
                full_header_six = f.read(6)
                # removes (from left to right) .docx, .jar, ZLock pro encrypted, and epub files from the file pool.
                if full_header_seven != b'\x50\x4B\x03\x04\x14\x00\x06' and full_header_seven != b'\x50\x4B\x03\x04\x14\x00\x08' \
                     and full_header_seven != b'\x50\x4B\x03\x04\x14\x00\x01' and full_header_six != b'\x50\x4B\x03\x04\x0A\x00':
                    f.seek(header + 18) # this is where the file length is stored
                    compressed_file_sizes.append(struct.unpack('<I', f.read(4))[0])

                    f.seek(header + 26)
                    filename_length = f.read(2)
                    filename_length_padded = bytearray(filename_length)
                    filename_length_padded.extend(b'\x00\x00')
                    filename_length = struct.unpack('<I', filename_length_padded)[0]
                    filename_length_list.append(filename_length)
                    
                    f.seek(header + 30)
                    filenames.append(f.read(filename_length))
                
                    header_offsets_temp.append(header)
                offset = header + 4

        #starting from each header, find the footer
        for i in range(len(header_offsets_temp)):
            comment_size = 0
            offset = header_offsets_temp[i]
            footer = mm.find(bytes(filenames[i]), offset + (compressed_file_sizes[i] - 22 - filename_length_list[i]))
            second_footer_part = mm.find(b'\x50\x4B', footer + filename_length_list[i])
            third_footer_part = mm.find(b'\x00\x00\x00', second_footer_part + 19, second_footer_part + 23)

            if footer != -1 and second_footer_part != -1:
                if third_footer_part == -1:
                    f.seek(second_footer_part + 20)
                    comment_size = f.read(1)
                footer_offsets.append(second_footer_part)
                header_offsets_final.append(header_offsets_temp[i])
            else:
                print(f'ZIP file header at {header_offsets_temp[i]} has no associated footer or its footer is invalid')


        for i in range(len(header_offsets_final)):
            files.append({'start': header_offsets_final[i], 'end': footer_offsets[i] + 22 + comment_size})
        
        # Remove false positives from file pool
        for file_pos in range(len(files)):
            do_not_add = False

            for file_start_check in files[file_pos:]:
                if file_start_check['start'] < files[file_pos]['end'] and file_start_check['start'] > files[file_pos]['start']:
                    do_not_add = True

            for file_end_check in files[:file_pos]:
                if file_end_check['end'] > files[file_pos]['start'] and file_end_check['end'] < files[file_pos]['end']:
                    do_not_add = True
            
            if do_not_add != True:
                final_files.append({'start': files[file_pos]['start'], 'end': files[file_pos]['end']})
        

        for i in range(len(final_files)):
            print(f'ZIP file found at {final_files[i]["start"]}, {final_files[i]["end"]}')

            zip_file = File(PREFIX, 'zip', source)
            zip_file.start = final_files[i]["start"]
            zip_file.end = final_files[i]["end"]
            list.append(zip_file)

    return list

# start
if __name__ == '__main__':
    main()