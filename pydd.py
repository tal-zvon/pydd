#!/usr/bin/env python3

###########
# Imports #
###########

import re
import os
import sys
import argparse
import textwrap
from pathlib import Path

###############
# Global Vars #
###############

# Bash color escape codes
RED='\033[00;31m'
NORMAL='\033[0m'

#############
# Functions #
#############

def blockdev_size(path):
    """
        Return block device size in bytes
        Source: https://stackoverflow.com/a/57137214/6423456
    """

    with open(path, 'rb') as f:
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
        # Try to figure it out
        if args.input_file == "/dev/stdin":
            # Input is a pipe - we don't know unless we were told
            # explicitly using the --ts arg. If the user didn't specify
            # --ts, args.ts will be None, so bytes_to_read will be set
            # to None
            bytes_to_read = args.ts
        else:
            # Check the type of file it is
            if input_file.is_block_device():
                # This is a block device
                print(f"{args.input_file} is a block device")
                bytes_to_read = blockdev_size(args.input_file)
            elif input_file.is_file():
                # This is a regular file
                print(f"{args.input_file} is a regular file")
                bytes_to_read = os.stat(args.input_file).st_size
            else:
                # This is an unsupported file type
                eprint(f"{args.input_file} is an unsupported filetype")
                sys.exit(1)

    print(args)
    print(f"Bytes to Read: {bytes_to_read}")
