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

# Number of bytes written
BYTES_WRITTEN = 0

# Start time
START_TIME = 0

##################
# Ctrl+C Handler #
##################

# Define the handler
def signal_handler(*args):
    print("\n")
    show_results()
    sys.exit(0)

# Register the handler
signal.signal(signal.SIGINT, signal_handler)

#############
# Functions #
#############

def update_status(bytes_written, total_bytes, elapsed_time):
    """
        Given some info about current progress, prints a progress bar

        Params:
            bytes_written:
                int of how many bytes have been written so far

            total_bytes:
                int of how many bytes there are in total
                None if unknown

            elapsed_time:
                seconds we've been writing for up to this point
    """

    if elapsed_time > 60:
        print(f"{bytes_written} bytes ({sizeof_fmt(bytes_written)}) copied, {human_readable_time(elapsed_time)} ({elapsed_time:.2f} s), {rate(bytes_written, elapsed_time)}")
    else:
        print(f"{bytes_written} bytes ({sizeof_fmt(bytes_written)}) copied, {elapsed_time:.2f} s, {rate(bytes_written, elapsed_time)}")

def sizeof_fmt(num, suffix='B'):
    """
        Converts filesize to human-readable form
        Source: https://stackoverflow.com/a/1094933/6423456
    """

    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0

    return "%.1f%s%s" % (num, 'Yi', suffix)

def show_results():
    """
        Shows how much data we've written, and how much time has elapsed
    """

    current_time = time.perf_counter()
    elapsed_time = current_time - START_TIME

    if elapsed_time > 60:
        print(f"{BYTES_WRITTEN} bytes ({sizeof_fmt(BYTES_WRITTEN)}) copied, {human_readable_time(elapsed_time)} ({elapsed_time:.2f} s), {rate(BYTES_WRITTEN, elapsed_time)}")
    else:
        print(f"{BYTES_WRITTEN} bytes ({sizeof_fmt(BYTES_WRITTEN)}) copied, {elapsed_time:.2f} s, {rate(BYTES_WRITTEN, elapsed_time)}")

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
    # Note: If the output file doesn't exist, make sure we have
    # permissions to write to the dir
    if output_file.exists():
        if not os.access(output_file, os.W_OK):
            eprint(f"No permission to write to {output_file}")
            sys.exit(1)
    else:
        output_dir = output_file.parent
        if not os.access(output_dir, os.W_OK):
            eprint(f"No permission to create {output_file}")
            sys.exit(1)

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
        passed (in seconds), calculates the rate, and returns a
        human-readable string
    """

    Bps = bytes_written / elapsed_time
    return f"{sizeof_fmt(Bps)}/s"

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
    help="Total size in bytes (allows us to show progress when using pipes)")

parser.add_argument(
    "--count", metavar="BLOCKS",
    type=int,
    help="Number of blocks to transfer")

parser.add_argument(
    "--seek", metavar="BLOCKS",
    type=int,
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

    # Make sure we aren't being asked to seek on a character device
    if input_file.is_char_device() and args.seek:
        eprint(f"{input_file} is a character device - cannot seek it")
        sys.exit(1)

    # Figure out amount of data we want to read/write
    if args.count:
        # We were told explicitly how much data to read
        BYTES_TO_WRITE = args.bs * args.count
    else:
        # Check the type of file it is
        if input_file.is_block_device():
            # This is a block device
            BYTES_TO_WRITE = blockdev_size(input_file)
        elif input_file.is_file():
            # This is a regular file
            BYTES_TO_WRITE = input_file.stat().st_size
        elif input_file.is_char_device():
            # This is a character device - we don't know the number
            # of bytes to read
            BYTES_TO_WRITE = None
        else:
            # This is an unsupported file type
            eprint(f"{input_file} is an unsupported filetype")
            sys.exit(1)

    ###################
    # Read/Write Data #
    ###################

    START_TIME = time.perf_counter()
    last_status_update = time.perf_counter()

    # Open source for reading, and destination for writing
    with input_file.open(mode="rb") as src, output_file.open(mode="wb") as dst:
        # Seek if we need to
        if args.seek:
            src.seek(args.seek)

        # Write data
        while True:
            if BYTES_TO_WRITE is None:
                buf_size = args.bs
            else:
                data_left = BYTES_TO_WRITE - BYTES_WRITTEN

                if data_left < args.bs:
                    buf_size = data_left
                else:
                    buf_size = args.bs

            # Check if we're done
            if not buf_size:
                break

            # Write buf data
            buf = src.read(buf_size)
            dst.write(buf)

            # Record the total data written
            BYTES_WRITTEN += buf_size

            # Update status
            now = time.perf_counter()
            if now - last_status_update > 1.0:
                current_time = time.perf_counter()
                elapsed_time = current_time - START_TIME

                update_status(BYTES_WRITTEN, BYTES_TO_WRITE, elapsed_time)
                last_status_update = now

    # Show user the results
    show_results()
