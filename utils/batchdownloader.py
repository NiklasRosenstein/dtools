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
import nr.futures
import requests
import urllib.parse

class BatchDownloader(object):

  def __init__(self, num_workers=1, logger=None):
    self.pool = nr.futures.ThreadPool(num_workers)
    self.logger = logger or logging

  def __download(self, url, ofile, desc, done_callback, future):
    try:
      response = requests.get(url, stream=True)
      response.raise_for_status()
    except Exception as exc:
      self.logger.error(exc)
      if done_callback:
        done_callback()
      return

    self.logger.info('Downloading "%s" ...', desc)
    content_length = response.headers.get('Content-length')
    if content_length is not None:
      content_length = int(content_length)

    bytes_read = 0
    try:
      exc = None
      with open(ofile, 'wb') as fp:
        for chunk in response.iter_content(chunk_size=1024):
          if future.cancelled():
            self.logger.info('Aborting download "%s"', desc)
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
        done_callback()

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, exc_tb):
    if exc_value is not None:
      self.pool.cancel()
    self.pool.shutdown(False)
    # Busy wait for the pool to complete so that we can catch keyboard
    # interrupts and cancel the downloads.
    try:
      while not self.pool.wait(1):
        pass
    except:
      self.pool.cancel()
      self.pool.wait()
      raise

  def stop(self):
    self.pool.cancel()
    self.pool.shutdown()

  def submit(self, url, ofile, desc=None, done_callback=None):
    if not desc:
      desc = posixpath.basename(urllib.parse.urlparse(url).path)
    future = nr.futures.Future()
    future.bind(self.__download, url, ofile, desc, done_callback, future)
    self.pool.enqueue(future)
    return future
