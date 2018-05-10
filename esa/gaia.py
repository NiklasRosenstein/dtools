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

from functools import partial
from itertools import islice

import argparse
import bs4
import logging
import gzip
import os
import posixpath
import requests
import shutil
import urllib.parse

import {BatchDownloader} from '../utils/batchdownloader'

logger = logging.getLogger(__name__)


def scrape_urls(directory):
  response = requests.get(directory)
  response.raise_for_status()
  doc = bs4.BeautifulSoup(response.text, 'lxml')
  for link in doc.find_all('a'):
    if '..' not in link['href']:
      yield urllib.parse.urljoin(directory + '/', link['href'])


def get_argument_parser(prog=None):
  parser = argparse.ArgumentParser(prog=prog, description='''
    Download table parts from the ESA GAIA Data Archive.
  ''')
  parser.add_argument('path', help='The path to the folder to download from, for example Gaia/gdr2/gaia_source/csv')
  parser.add_argument('--begin', type=int, help='Slice begin from the download list.')
  parser.add_argument('--end', type=int, help='Slice end from the download list.')
  parser.add_argument('--parallel', type=int, default=1, help='Enable parallel downloads.')
  parser.add_argument('--print-urls', action='store_true', help='Print the download list.')
  parser.add_argument('--to', help='Destination download folder. Default is the current working directory.')
  parser.add_argument('--unpack', action='store_true', help='Automatically unpack downloaded archives.')
  parser.add_argument('--overwrite-existing', action='store_true', help='Overwrite existing files.')
  return parser


def main(argv=None, prog=None):
  parser = get_argument_parser(prog)
  args = parser.parse_args(argv)
  logging.basicConfig(level=logging.INFO, format='[%(levelname)s - %(asctime)s]: %(message)s')

  logger.info('Retrieving URL list ...')
  urls = scrape_urls('http://cdn.gea.esac.esa.int/' + args.path)
  urls = islice(urls, args.begin, args.end)

  if args.print_urls:
    for url in urls:
      print(url)
    return

  if args.to and not os.path.isdir(args.to):
    logger.info('Creating directory "{}"'.format(args.to))
    os.makedirs(args.to)

  try:
    with BatchDownloader(args.parallel, logger) as downloader:
      def download_finished(output_file):
        if output_file.endswith('.gz') and args.unpack:
          logger.info('Unpacking "%s" ...', os.path.basename(output_file))
          with gzip.open(output_file) as src:
            with open(output_file[:-3], 'wb') as dst:
              shutil.copyfileobj(src, dst)
          os.remove(output_file)

      for url in urls:
        basename = posixpath.basename(urllib.parse.urlparse(url).path)
        outfile = os.path.join(args.to, basename) if args.to else basename
        if os.path.isfile(outfile) and not args.overwrite_existing:
          logger.info('Skipping "%s"', basename)
          continue

        downloader.submit(url, outfile,
          done_callback=partial(download_finished, outfile))
  except KeyboardInterrupt:
    logger.info('Aborted.')

if require.main == module:
  main()
