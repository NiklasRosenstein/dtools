# Copyright (c) 2017  Niklas Rosenstein
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
"""

from urllib.parse import urlparse
import argparse
import click
import collections
import csv
import logging
import os
import posixpath
import re
import requests
import shlex
import sys

wget_parser = argparse.ArgumentParser()
wget_parser.add_argument('-O')
wget_parser.add_argument('-a')
wget_parser.add_argument('url')

WgetCommand = collections.namedtuple('WgetCommand', 'url ofile logfile')
logger = logging.getLogger(__name__)


def parse_batch_file(filename):
  printed_warning = False
  with open(filename) as fp:
    for line in fp:
      line = line.strip()
      if not line or line.startswith('#'): continue
      if not line.startswith('wget'):
        if not printed_warning:
          logger.warn('file "%s" contains commands that are not "wget".', filename)
          printed_warning = True
        continue
      # TODO: Catch exception on parse error.
      args = wget_parser.parse_args(shlex.split(line)[1:])
      yield WgetCommand(args.url, args.O, args.a)


@click.group()
def main():
  logging.basicConfig(level=logging.INFO, format='[%(levelname)s - %(asctime)s]: %(message)s')


@main.command('extract-urls')
@click.argument('files', nargs=-1)
@click.option('-F', '--format', type=click.Choice(['url', 'csv']),
  help='The output format.'
)
@click.pass_context
def extract_urls(ctx, files, format):
  """
  Extract all URLs from NASA-ExAr .bat files.

  One or more filename must be specified. The files must be .bat files
  downloaded from the NASA Exoplanet Archive Bulk Download website that
  contain 'wget' commands for the file download.

  If the output format 'csv' is selected, the output CSV data does not
  have a header row and its columns are: url|ofile|logfile.
  """

  if not files:
    ctx.fail('no input files')
  if format == 'csv':
    writer = csv.writer(sys.stdout)

  for filename in files:
    for wget in parse_batch_file(filename):
      if format == 'csv':
        writer.writerow(wget)
      else:
        print(wget.url)


@main.command('bulk-download')
@click.argument('files', nargs=-1)
@click.option('--to', help='The output directory.')
@click.option('--overwrite-existing', is_flag=True, help='Overwrite existing files.')
@click.pass_context
def bulk_download(ctx, files, to, overwrite_existing):
  """
  Execute the bulk download from NASA-ExAr .bat files without using 'wget'.
  """

  if not files:
    ctx.fail('no input files')

  if to and not os.path.isdir(to):
    os.makedirs(to)

  for filename in files:
    for wget in parse_batch_file(filename):
      output_file = wget.ofile
      if not output_file:
        output_file = posixpath.basename(urlparse(wget.url).path)
      output_file_base = output_file
      if to:
        output_file = os.path.join(to, output_file)
      if not overwrite_existing and os.path.isfile(output_file):
        logger.info('Skipping "%s"', output_file)
        continue

      logger.info('Downloading "%s" ...', output_file)
      response = requests.get(wget.url)
      try:
        response.raise_for_status()
      except Exception as exc:
        logger.error(exc)
        continue

      try:
        with open(output_file, 'wb') as fp:
          for chunk in response.iter_content(chunk_size=1024):
            fp.write(chunk)
      except KeyboardInterrupt:
        # Do not keep half-completed files.
        if os.path.isfile(output_file):
          logger.warn('Removing incomplete download: "%s"', output_file)
          os.remove(output_file)
        raise


if require.main == module:
  main()
