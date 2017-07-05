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

from typing import Iterable
import click
import functools
import itertools
import logging
import gzip
import os
import posixpath
import shutil
import urllib.parse
import {BatchDownloader} from '../utils/batchdownloader'

logger = logging.getLogger(__name__)


def generate_download_urls(
  root:str, source:str, format:str,
  range1:Iterable, range2:Iterable, range3:Iterable
):
  """
  Generates download URLs from the ESA (European Space Agency) content
  delivery network (http://cdn.gea.esac.esa.int/).

  # Parameters
  root: "Gaia" or "gdr1" (both the same thing).
  source: "gaia" or "tgas"
  format: "csv", "fits" or "votable"
  range1: Iterable yielding numbers between 000 and 999.
  range2: See *range1*.
  range3: See *range1*.
  """

  if root not in ('Gaia', 'gdr1'):
    raise ValueError('invalid root: {!r}'.format(root))
  if source not in ('gaia', 'tgas'):
    raise ValueError('invalid source: {!r}'.format(source))
  if format not in ('csv', 'fits', 'votable'):
    raise ValueError('invalid format: {!r}'.format(format))

  if format == 'csv':
    suffix = '.csv.gz'
  elif format == 'fits':
    suffix = '.fits'
  elif format == 'votable':
    suffix = '.vot.gz'
  else: assert False

  url = 'http://cdn.gea.esac.esa.int/' + root + '/' + source + '_source/'
  url = url + format + '/' + source[0].upper() + source[1:] + 'Source_'

  for x, y, z in itertools.product(range1, range2, range3):
    yield url + '{:03d}-{:03d}-{:03d}'.format(x, y, z) + suffix


def parse_range(string):
  try:
    if '-' in string:
      parts = string.split('-')
      if len(parts) != 2:
        raise ValueError
      start, end = map(int, parts)
    else:
      start = end = int(string)
  except ValueError:
    raise ValueError('invalid range: {!r}'.format(string)) from None
  return range(start, end+1)


@click.command()
@click.option('--parallel', type=int, default=1, help='Parallel downloads.')
@click.option('--source', default='gaia', type=click.Choice(['gaia', 'tgas']))
@click.option('--format', default='csv', type=click.Choice(['csv', 'fits', 'votable']))
@click.option('--root', default='gdr1', type=click.Choice(['gdr1', 'Gaia']))
@click.option('--range1', type=parse_range)
@click.option('--range2', type=parse_range)
@click.option('--range3', type=parse_range)
@click.option('--generate-urls', is_flag=True)
@click.option('--to', help='Destination download folder.')
@click.option('--unpack/--no-unpack', default=False, help='Unpack downloaded archives.')
@click.option('--overwrite-existing', is_flag=True)
def main(parallel, source, format, root, range1, range2, range3, generate_urls, to, unpack, overwrite_existing):
  logging.basicConfig(level=logging.INFO, format='[%(levelname)s - %(asctime)s]: %(message)s')

  if range1 is None:
    range1 = range(1)
  if range2 is None:
    range2 = range(0, 21) if source == 'gaia' else range(1)
  if range3 is None:
    range3 = range(0, 256) if source == 'gaia' else range(16)

  urls = generate_download_urls(root, source, format, range1, range2, range3)
  if generate_urls:
    for url in urls:
      print(url)
    return

  if to and not os.path.isdir(to):
    os.makedirs(to)

  def download_finished(output_file):
    if output_file.endswith('.gz') and unpack:
      logger.info('Unpacking "%s" ...', os.path.basename(output_file))
      with gzip.open(output_file) as src:
        with open(output_file[:-3], 'wb') as dst:
          shutil.copyfileobj(src, dst)
      os.remove(output_file)

  with BatchDownloader(parallel, logger) as downloader:
    for url in urls:
      basename = posixpath.basename(urllib.parse.urlparse(url).path)
      outfile = os.path.join(to, basename) if to else basename
      if os.path.isfile(outfile) and not overwrite_existing:
        logger.info('Skipping "%s"', basename)
        continue

      downloader.submit(url, outfile,
        done_callback=functools.partial(download_finished, outfile))


if require.main == module:
  main()
