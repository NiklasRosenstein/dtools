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

import os
import logging
import posixpath
import requests
import urllib.parse
import ThreadPool from './threadpool'

class BatchDownloader(object):

  def __init__(self, num_workers=1, logger=None):
    self.pool = ThreadPool(num_workers)
    self.logger = logger or logging

  def __downloader(self, url, ofile, desc, done_callback):
    self.logger.info('Downloading "%s" ...', desc)
    try:
      response = requests.get(url)
      response.raise_for_status()
    except Exception as exc:
      logger.error(exc)
      if done_callback:
        done_callback(url, ofile, exc)
      return

    content_length = response.headers.get('Content-length')
    if content_length is not None:
      content_length = int(content_length)

    bytes_read = 0
    try:
      exc = None
      with open(ofile, 'wb') as fp:
        for chunk in response.iter_content(chunk_size=1024):
          if not self.pool.running:
            raise KeyboardInterrupt
          fp.write(chunk)
          bytes_read += len(chunk)
    except KeyboardInterrupt:
      # TODO: Delete ofile
      if os.path.isfile(ofile):
        try:
          os.remove(ofile)
        except OSError as exc:
          self.logger.error('Could not remove incomplete file "%s": %s', ofile, exc)
        else:
          self.logger.info('Removed incomplete file "%s"', ofile)
      return
    except Exception as _exc:
      exc = _exc
      self.logger.error(exc)
    finally:
      if done_callback:
        done_callback(url, ofile, exc)

  def __enter__(self):
    self.pool.start()
    return self

  def __exit__(self, *args):
    self.pool.stop()

  def stop(self):
    self.pool.stop()

  def submit(self, url, ofile, desc=None, done_callback=None):
    if not desc:
      desc = posixpath.basename(urllib.parse.urlparse(url).path)
    self.pool.submit(self.__downloader, url, ofile, desc, done_callback)


exports = BatchDownloader
