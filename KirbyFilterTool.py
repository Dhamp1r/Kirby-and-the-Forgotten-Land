"""Kirby and the Forgotten Land Filter Tool

   Author: Dhampir
   Version: 1.0
   License: MIT
"""

import os
import struct
import argparse


def padding_calc(number, offset):
    padding = number - (offset % number)
    if padding == number != 4:
        return 0
    else:
        return padding


def convert_file_content(content):
    converted_content = []
    for char in content:
        converted_content.append(struct.pack('H', ord(char)))
    return converted_content


def pack_files(input_folder, output_path):
    files_to_pack = os.listdir(input_folder)
    files_to_pack.sort(key=lambda x: int(x.split('_')[0]))
    placeholders_offsets = []
    names_offsets = []

    num_files = len(files_to_pack)

    with open(output_path, 'wb') as packed_file:
        packed_file.write(b'XBIN')
        packed_file.write(b'\x34\x12\x04\x00')
        packed_file.write(b'\x00' * 4)
        packed_file.write(b'\xE9\xFD\x00\x00')
        packed_file.write(b'\x00' * 4)
        packed_file.write(struct.pack('I', num_files))
        packed_file.write(struct.pack('I', 0) * num_files)
        packed_file.write(padding_calc(32, packed_file.tell()) * b'\x00')

        for idx, filename in enumerate(files_to_pack):
            placeholders_offsets.append(packed_file.tell())
            packed_file.write(struct.pack('4B', 0, 0, 0, 0))
            file_path = os.path.join(input_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as input_file:
                content = input_file.read()
                packed_file.write(struct.pack('I', len(content)))
                converted_content = convert_file_content(content)
                for char in converted_content:
                    packed_file.write(char)
                if idx != len(files_to_pack) - 1:
                    packed_file.write(padding_calc(32, packed_file.tell()) * b'\x00')

        for filename in files_to_pack:
            name = os.path.splitext(filename.split('_')[1])[0]
            name_offset = packed_file.tell()
            names_offsets.append(name_offset)
            name_length = len(name)
            packed_file.write(struct.pack('I', name_length))
            packed_file.write(name.encode('utf-8'))
            if filename != files_to_pack[-1]:
                packed_file.write(padding_calc(4, packed_file.tell()) * b'\x00')

        packed_file.write(padding_calc(4, packed_file.tell()) * b'\x00')
        end_file = packed_file.tell()
        packed_file.write(b'\x52\x4C\x4F\x43\x00\x00\x00\x00\x00\x00\x00\x00')

        for offset in placeholders_offsets:
            packed_file.seek(offset)
            name_offset = names_offsets.pop(0)
            packed_file.write(struct.pack('I', name_offset))

        packed_file.seek(24)
        for offset in placeholders_offsets:
            packed_file.write(struct.pack('I', offset))
        packed_file.seek(16)
        packed_file.write(struct.pack('I', end_file))
        packed_file.seek(8)
        packed_file.write(struct.pack('I', end_file - 1))


def unpack_files(input_path, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(input_path, 'rb') as file:
        magic = file.read(4)
        version = file.read(4)
        end_file = file.read(4)
        dummy = file.read(4)
        start_rloc = file.read(4)

        num_files = struct.unpack('I', file.read(4))[0]

        for i in range(num_files):
            offset = struct.unpack('I', file.read(4))[0]

        file.read(padding_calc(32, file.tell()))
        for j in range(num_files):
            name_offset = struct.unpack('I', file.read(4))[0]
            current_position = file.tell()
            file.seek(name_offset)
            name_len = struct.unpack('I', file.read(4))[0]
            name = file.read(name_len).decode()
            file.seek(current_position)
            count_char = struct.unpack('I', file.read(4))[0]

            output_file_path = os.path.join(output_folder, f"{file.tell()}_{name}.txt")

            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                for _ in range(count_char):
                    char = chr(struct.unpack('H', file.read(2))[0])
                    output_file.write(char)

            file.read(padding_calc(32, file.tell()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pack/Unpack files in a folder into/from a binary file')
    parser.add_argument('mode', choices=['pack', 'unpack'], help='Mode: pack/unpack')
    parser.add_argument('input_path', help='Path to the input file/folder')
    parser.add_argument('output_path', help='Path to the output file/folder')
    args = parser.parse_args()

    if args.mode == 'pack':
        pack_files(args.input_path, args.output_path)
    elif args.mode == 'unpack':
        unpack_files(args.input_path, args.output_path)
