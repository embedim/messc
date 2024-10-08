import argparse
from messc_core import *

def main():
    parser = argparse.ArgumentParser(description="Mess in C")
    parser.add_argument("-i", "--input", nargs='+', required=True, help="Input files")
    parser.add_argument("-p", "--prep", choices=['0', '1'],nargs='?', default=0, help=f'Preparation data')
    parser.add_argument("-o", "--output", nargs='?', default='output', help=f'Output dir')

    compression_modes = ['zlib', 'bz2', 'lzma']
    parser.add_argument(
        '-c',
        '--compressor',
        choices=compression_modes,
        nargs='?',
        default=compression_modes[0],
        help=f'Using compressor, default {compression_modes[0]}'
    )

    parser.add_argument('--loglevel', default='INFO',
                    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                    help='Logging level (default: INFO)')

    mess_process(parser.parse_args())


if __name__ == "__main__":
    main()