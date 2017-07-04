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

import functools
import queue
import threading
import traceback


class ThreadPool(object):
  """
  Represents a pool for threads that. Note that if only one worker is
  specified via *num_workers*, no thread will actually be spawned and
  the queued functions are executed immediately, unless *optimize* is
  set to #False.

  If *block* is #True (default), putting new items on the threadpool
  when there is no thread currently available will block until a thread
  becomes available.
  """

  def __init__(self, num_workers=1, optimize=True, error_handler=None,
               block=True):
    if num_workers < 1:
      raise ValueError('invalid num_workers: {!r}'.format(num_workers))
    self.num_workers = num_workers
    self.optimize = optimize
    self.queue = queue.Queue(num_workers if block else 0)
    self.threads = None
    self.error_handler = error_handler
    self._running = threading.Event()

  @property
  def running(self):
    return self._running.is_set()

  def __enter__(self):
    " Start all threads in the pool. "

    if self.num_workers == 0 and self.optimize:
      return
    if self.threads is not None:
      raise RuntimeError('ThreadPool is not reentrant.')
    self.threads = [
      threading.Thread(target=self.__worker, args=[i])
      for i in range(self.num_workers)
    ]
    [t.start() for t in self.threads]
    self._running.set()
    return self

  def __exit__(self, *args):
    " Blocks until all threads are finished. "

    if self.threads is not None:
      self._running.clear()
      [self.queue.put(None) for i in range(self.num_workers)]
      [t.join() for t in self.threads]
      self.threads = None

  start = __enter__
  stop = __exit__

  def __worker(self, index):
    while True:
      func = self.queue.get()
      if func is None or not self.running:
        break
      try:
        func()
      except BaseException as exc:
        if self.error_handler:
          self.error_handler(exc)
        else:
          if not isinstance(exc, KeyboardInterrupt):
            traceback.print_exc()

  def submit(self, __function, *args, **kwargs):
    if self.num_workers == 1 and self.optimize:
      __function(*args, **kwargs)
    else:
      func = functools.partial(__function, *args, **kwargs)
      self.queue.put(func)


exports = ThreadPool
