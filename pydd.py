#!/usr/bin/env python3

###########
# Imports #
###########

import argparse
import textwrap

###############
# Global Vars #
###############

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
    default="4M")

parser.add_argument(
    "--ts", "--total-size",
    metavar="SIZE",
    help="Total size in bytes (for use with pipes)")

parser.add_argument(
    "--count", metavar="BLOCKS",
    help="Number of blocks to transfer")

parser.add_argument(
    "--seek", metavar="BLOCKS",
    help="Seek BLOCKS number of blocks before reading data")

# Parse sys.argv using the rules defined above
args = parser.parse_args()

