import re
import shutil
import zlib
import lzma
import bz2
import logging
import argparse
from pathlib import Path

logger = logging.getLogger(__name__)

mess_compresed_array_name = 'MESS_COMPRESSED_ARRAY'
mess_decompresed_array_name = 'MESS_DECOMPRESSED_ARRAY'
mess_replace = 'MESS_REPLACE'

class MessCore:
    def __init__(self, path, output = 'output'):
        self.count = -1
        self.list_b = []
        self.data = bytearray()
        self.position = {}

        self.compressed = bytearray()
        self.decompressor_code = ""

        self.dest_folder = Path(path) / output

        self.dest_folder.mkdir(parents=True, exist_ok=True)
        self.base_dir = Path(__file__).resolve().parent

        self.copy_files()

    def add_string(self, new_string):
        self.count = self.count + 1
        self.list_b.append(bytes(new_string))
        return self.count

    def process_match(self, match):
        string = match.group(1)
        string = re.sub(
            r'\\.', 
            lambda m: {
                '\\r': '\r',
                '\\n': '\n',
                '\\t': '\t',
                '\\b': '\b',
                '\\f': '\f',
                '\\a': '\a',
                '\\v': '\v',
                '\\0': '\0',
                '\\\\': '\\',
                "\\'": "'",
                '\\"': '"',
            }.get(m.group(0), m.group(0)),
            string
        )
        if len(string) < 3:
            return string
        string = string + '\0'
        string = string.encode('utf-8')
        current_count = self.add_string(string)

        return f'{mess_replace}_{current_count}'

    def create_file(self, file_name):
        logging.debug(f'file: {file_name}')

        new_lines = []
        multiline_comment = False
        with open(file_name, 'r') as file:
            lines = file.readlines()

        for line in lines:
            if re.search(r'#define.*MESS_INIT\(\)', line):
                new_lines.append('#include "mess.h"\n')
                continue

            if '#include' in line:
                new_lines.append(line)
                continue

            if '//' in line:
                left_part, right_part = line.split('//', 1)
                left_part = re.sub(r'"(.*?)"', self.process_match, left_part)
                new_lines.append(left_part + '//' + right_part)
                continue

            if '/*' in line:
                if '*/' not in line:
                    multiline_comment = True
                else:
                    left_part, right_part = line.split('/*', 1)
                    left_part = re.sub(r'"(.*?)"', self.process_match, left_part)
                    new_lines.append(left_part + '/*' + right_part)
                    continue

            if multiline_comment:
                new_lines.append(line)
                if '*/' in line:
                    multiline_comment = False
                continue

            new_line = re.sub(r'"(.*?)"', self.process_match, line)
            new_lines.append(new_line)

        path = Path(self.dest_folder) /  Path(file_name)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as file:
            file.writelines(new_lines)

    def one_pass(self):
        for i,value in enumerate(self.list_b):
            self.position.setdefault(i, len(self.data))
            self.data.extend(value)

        logging.debug(f'Found strings {len(self.list_b)}')

    def two_pass(self):
        string_uses = {}
        for value in self.list_b:
            curr_pos = len(self.data)
            get_pos = string_uses.setdefault(value, curr_pos)
            if get_pos == curr_pos:
                self.data.extend(value)

        for i,value in enumerate(self.list_b):
            self.position.setdefault(i, string_uses.get(value))

        logging.debug(f'Found strings {len(self.list_b)}')
        logging.debug(f'Unique strings {len(string_uses)}')

    def compress(self, compressor):
        logging.info(f"Original size: {len(self.data)}")

        if compressor == 'bz2':
            data = bz2.compress(self.data, compresslevel=9)
        elif compressor == 'lzma':
            data = lzma.compress(self.data, preset=9)
        else:
            data = zlib.compress(self.data, level=1)

        decompressor_file = Path(self.base_dir) / 'code' / 'decompressor' / f'{compressor}.c'

        if not decompressor_file.exists():
            raise FileNotFoundError(f"Decompressor file '{decompressor_file}' does not exist.")

        with open(decompressor_file, 'r') as file:
            self.decompressor_code = file.read()

        self.compressed = data
        logging.info(f'Compessed size: {len(data)}')

    def copy_files(self):
        sours = Path(self.base_dir)  /'code'/'headers'/'mess.h'
        dest = Path(self.dest_folder) / sours.name
        try:
            shutil.copy(sours, dest)
            logging.info(f"'Copied {sours.name}' to '{dest}'.")
        except Exception as e:
            logging.error(f"Failed to copy file: {e}")

    def generate_files(self):
        mess_data = Path(self.dest_folder) / 'mess_data.c'
        with open(mess_data,'w') as file:
            file.write(self.decompressor_code)
            file.write(f'\n//Generated array\n')
            file.write(f'char {mess_compresed_array_name}[] = {{\n')
            file.write(self._format_compressed_data())
            file.write('};\n\n')
            file.write(f'char {mess_decompresed_array_name}[{len(self.data)}];')

        mess_position = Path(self.dest_folder) / 'mess_position.h'
        with open(mess_position, 'w') as file:
            file.write("#pragma once\n\n")
            file.write(f"#define MESS_SIZE_ORIGIN_ARRAY  {len(self.data)}\n")
            file.write(f"#define MESS_SIZE_COMPRESED_ARRAY  {len(self.compressed)}\n\n")
            file.write(f"extern char  {mess_compresed_array_name}[];\n")
            file.write(f"extern char  {mess_decompresed_array_name}[];\n\n")
            for key, value in self.position.items():
                file.write(f"#define {mess_replace}_{key}    ({mess_decompresed_array_name} + {value})\n")

    def _format_compressed_data(self):
        return ',\n'.join(
            ','.join(f"0x{num:02x}" for num in self.compressed[i:i + 16])
            for i in range(0, len(self.compressed), 16)
        )


def mess_process(args):
    logging.basicConfig(level=args.loglevel)

    all_files = all(Path(path).is_file() and Path(path).suffix == '.c' for path in args.input)

    if all_files:
        current_dir = Path.cwd()
        hs = MessCore(current_dir, args.output)

        for file in args.input:
            hs.create_file(file)
        if args.prep == '1':
            hs.two_pass()
        else:
            hs.one_pass()
        hs.compress(args.compressor)
        hs.generate_files()

    else:
        logging.info(f'Wrong inputs files')

