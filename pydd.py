#!/usr/bin/env python3

###########
# Imports #
###########

import re
import os
import sys
import time
import signal
import argparse
import textwrap
from pathlib import Path

###############
# Global Vars #
###############

# Bash color escape codes
RED='\033[00;31m'
NORMAL='\033[0m'

# Number of bytes read
BYTES_READ = 0
BYTES_WRITTEN = 0

# Start time
START_TIME = 0

##################
# Ctrl+C Handler #
##################

# Define the handler
def signal_handler(*args):
    current_time = time.perf_counter()
    elapsed_time = current_time - START_TIME

    print(f"\n{BYTES_WRITTEN} bytes ({human_readable_size(BYTES_WRITTEN)}) copied, {human_readable_time(elapsed_time)} ({elapsed_time:.2f} s), {rate(BYTES_WRITTEN, elapsed_time)}")
    sys.exit(0)

# Register the handler
signal.signal(signal.SIGINT, signal_handler)

#############
# Functions #
#############

def blockdev_size(path):
    """
        Return block device size in bytes
        Source: https://stackoverflow.com/a/57137214/6423456
    """

    with path.open('rb') as f:
        return f.seek(0, 2) or f.tell()

def eprint(s, **kwargs):
    """
        Print to stderr
    """
    print(f"{RED}ERROR{NORMAL}: {s}", file=sys.stderr, **kwargs)

def permissions_check(input_file, output_file):
    """
        Make sure we have permissions to read from input_file, and write
        to output_file
    """

    # Make sure the input file exists
    if not input_file.exists():
        eprint(f"{input_file} does not exist")
        sys.exit(1)

    # Make sure we have the permissions to read from input_file
    if not os.access(input_file, os.R_OK):
        eprint(f"No permission to read {input_file}")
        sys.exit(1)

    # Make sure we have the permissions to write to output_file
    if not os.access(output_file, os.W_OK):
        eprint(f"No permission to write to {output_file}")
        sys.exit(1)

def human_readable_size(bytes):
    """
        Given an int (number of bytes), returns a human-readable string
        of the size
    """

    i = 0
    res = bytes
    while True:
        if res > 1024:
            res /= 1024
            i += 1
        else:
            break

    units = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]

    return f'{res:.2f} {units[i]}'

def human_readable_time(seconds):
    """
        Given the number of seconds, returns a human-readable string
        of seconds/minutes/hours/days

        Source: https://gist.github.com/borgstrom/936ca741e885a1438c374824efb038b3
    """

    TIME_DURATION_UNITS = (
        ('week', 60*60*24*7),
        ('day', 60*60*24),
        ('hour', 60*60),
        ('min', 60),
        ('sec', 1)
    )

    if seconds == 0:
        return '0 s'

    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{} {}{}'.format(amount, unit, "" if amount == 1 else "s"))
    return ', '.join(parts)

def rate(bytes_written, elapsed_time):
    """
        Given how much data was written (in bytes), and how much time has
        passed, calculates the rate, and returns a human-readable string
    """

    return '10 MB/s'

def size(s):
    """
        Validates that the data looks like a proper size value
        Returns the size in bytes
        Accepts suffixes:
          K - Kibibyte
          M - Mebibyte
          G - Gibibyte
          T - Tebibyte
          P - Pebibyte
          E - Exbibyte
          Z - Zebibyte
    """

    pattern = '^[0-9]+[kmgtpez]?$'

    # Make sure it looks right
    if not re.search(pattern, s, re.IGNORECASE):
        raise ValueError()

    # Convert to int value in bytes
    if s.isdigit():
        return int(s)
    elif 'k' in s.lower():
        return int(s[:-1]) * 1024
    elif 'm' in s.lower():
        return int(s[:-1]) * 1024 ** 2
    elif 'g' in s.lower():
        return int(s[:-1]) * 1024 ** 3
    elif 't' in s.lower():
        return int(s[:-1]) * 1024 ** 4
    elif 'p' in s.lower():
        return int(s[:-1]) * 1024 ** 5
    elif 'e' in s.lower():
        return int(s[:-1]) * 1024 ** 6
    elif 'z' in s.lower():
        return int(s[:-1]) * 1024 ** 7

#############
# Arguments #
#############

# Define parser
parser = argparse.ArgumentParser(
    # Allows newlines in epilog
    formatter_class=argparse.RawDescriptionHelpFormatter,

    # Adds additional text to the end of the help string
    epilog=textwrap.dedent("""
    Sizes:
        Sizes for --bs and --ts can either be specified in bytes, or
        with suffixes. Ex:
            1024    # 1024 bytes
            1M      # 1 Megabyte (1024 bytes)
            1G      # 1 Gigabyte (1024 Megabytes)
"""))

# Add Arguments #

# Note: You can't have an attribute called if (args.if), so it must be
# renamed with 'dest'
parser.add_argument(
    "--if", "--input-file",
    metavar="FILE",
    help="Input file to read from (Default: stdin)",
    default="/dev/stdin",
    dest="input_file")

# Since '--if' must be renamed (see above), might as well rename '--of' too
parser.add_argument(
    "--of", "--output-file",
    metavar="FILE",
    help="Output file to write to (Default: stdout)",
    default="/dev/stdout",
    dest="output_file")

parser.add_argument(
    "--bs", "--block-size",
    metavar="SIZE",
    help="Specify the blocksize (Default: 4M)",
    type=size,
    default="4M")

parser.add_argument(
    "--ts", "--total-size",
    metavar="SIZE",
    type=size,
    help="Total size in bytes (for use with pipes)")

parser.add_argument(
    "--count", metavar="BLOCKS",
    type=int,
    help="Number of blocks to transfer")

parser.add_argument(
    "--seek", metavar="BLOCKS",
    help="Seek BLOCKS number of blocks before reading data")

########
# Main #
########

if __name__ == "__main__":
    # Parse sys.argv using the rules defined above
    args = parser.parse_args()

    # Turn input file and output file into pathlib Path objects
    input_file = Path(args.input_file)
    output_file = Path(args.output_file)

    # Ensure permissions for reading from source, and writing to dest
    permissions_check(input_file, output_file)

    # Figure out amount of data we want to read
    if args.count:
        # We were told explicitly how much data to read
        bytes_to_read = args.bs * args.count
    else:
        # Check the type of file it is
        if input_file.is_block_device():
            # This is a block device
            bytes_to_read = blockdev_size(input_file)
        elif input_file.is_file():
            # This is a regular file
            bytes_to_read = input_file.stat().st_size
        elif input_file.is_char_device():
            # This is a character device - we don't know the number
            # of bytes to read
            bytes_to_read = None
        else:
            # This is an unsupported file type
            eprint(f"{input_file} is an unsupported filetype")
            sys.exit(1)

    # Read/Write data
    START_TIME = time.perf_counter()

    with input_file.open(mode="rb") as src, output_file.open(mode="w") as dst:
        time.sleep(10)
