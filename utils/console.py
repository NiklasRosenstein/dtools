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
Simple wrapper for terminal cursor positioning and coloring.
"""

try:
  import blessed
except ImportError:
  blessed = None

try:
  import fcntl, termios
except ImportError:
  fcntl = termios = None

import abc
import errno
import colorama
import contextlib
import ctypes
import os
import struct
import sys

colorama.init()

## API ##
#########

class BaseConsole(metaclass=abc.ABCMeta):

  #: A dictionary with all color control characters.
  colors = dict(
    [(k.lower(), v) for k, v in vars(colorama.Fore).items()] +
    [('on_' + k.lower(), v) for k, v in vars(colorama.Back).items()]
  )

  #: A dictionary with all style control characters.
  styles = dict(
    [(k.lower(), v) for k, v in vars(colorama.Style).items()]
  )

  def __getattribute__(self, name):
    """
    Returns a member of the #colors or #styles dictionary if #isatty is
    #True, otherwise an empty string is returned.
    """

    value = BaseConsole.colors.get(name)
    if value is None:
      value = BaseConsole.styles.get(name)
    if value is not None:
      return value

    return object.__getattribute__(self, name)

  @abc.abstractmethod
  def update(self):
    """
    Should be called before any other method is used or property being
    retrieved.
    """

  @abc.abstractproperty
  def screen_size(self):
    """
    Retrieves the terminal size in (x, y) coordinates.
    """

  @abc.abstractproperty
  def screen_offset(self):
    """
    Returns the terminal screen offset in the terminal buffer. Adding this
    to the #size gives the buffer size.
    """

  @abc.abstractproperty
  def buffer_size(self):
    """
    Retrieves the buffer size (x, y) coordinates.
    """

  @abc.abstractproperty
  def location(self):
    """
    Returns a tuple of (x, y) coordinates relative to the terminal screen.
    """

  @abc.abstractmethod
  def location_in_buffer(self):
    """
    Returns a tuple of absolute (x, y) coordinates inside the buffer.
    """

  @abc.abstractproperty
  def isatty(self):
    """
    Returns True if the console is a terminal device. If this is false, all
    the operations on the #BaseConsole have no effect.
    """

  @abc.abstractmethod
  def move(self, x=None, y=None):
    """
    Set the current cursor coordinates in terminal screen coordinates. *x*
    and *y* can both be omitted when the cursor position should not be
    modified.
    """

  @abc.abstractmethod
  def move_in_buffer(self, x=None, y=None):
    """
    Set the current cursor coordinates from absolute buffer coordinates.
    """

  @contextlib.contextmanager
  def movectx(self, x=None, y=None):
    """
    Context-manager that sets the current cursor position and restores it
    on exit. The default implementation retrieves the original cursor
    position with #location and sets it back with #move().
    """

    pos = self.location
    self.move(x, y)
    try:
      yield
    finally:
      self.move(*pos)

  @contextlib.contextmanager
  def movectx_in_buffer(self, x=None, y=None):
    """
    Same as #movectx() but uses #move_in_buffer() and #location_in_buffer.
    """

    pos = self.location_in_buffer
    self.move_in_buffer(x, y)
    try:
      yield
    finally:
      self.move_in_buffer(*pos)

  def title(self, title):
    """
    Sets the title of the terminal.
    """

    sys.stderr.write('\033]0;' + title + '\007')


## Blessed (requires Curses) ##
###############################

class BlessedConsole(BaseConsole):

  def __init__(self):
    if not fcntl:
      raise ImportError('fcntl not available')
    if not termios:
      raise ImportError('termios not available')
    if not blessed:
      raise ImportError('blessed not available')
    self._term = blessed.Terminal()

  @property
  def size(self):
    if not self._term.is_a_tty:
      return (0, 0)
    return self._term._height_and_width()

  @property
  def offset(self):
    if not self._term.is_a_tty:
      return (0, 0)
    # TODO
    return (0, 0)

  @property
  def isatty(self):
    return self._blessed.is_a_tty

  @property
  def location(self):
    if not self._term.is_a_tty:
      return (0, 0)
    return self._term.get_location()

  def move(self, x=None, y=None):
    if not self._term.is_a_tty:
      return
    self._term.move(x, y)


## Windows ##
#############

class _COORD(ctypes.Structure):
  _fields_ = [
    ('x', ctypes.c_int16),
    ('y', ctypes.c_int16)
  ]


class _SMALL_RECT(ctypes.Structure):
  _fields_ = [
    ('left', ctypes.c_int16),
    ('top', ctypes.c_int16),
    ('right', ctypes.c_int16),
    ('bottom', ctypes.c_int16)
  ]


class _CONSOLE_SCREEN_BUFFER_INFO(ctypes.Structure):
  _fields_ = [
    ('dwSize', _COORD),
    ('dwCursorPosition', _COORD),
    ('wAttributes', ctypes.c_int16),
    ('srWindow', _SMALL_RECT),
    ('dwMaximumWindowSize', _COORD)
  ]


class WindowsConsole(BaseConsole):

  def __init__(self):
    if sys.stderr.isatty():
      self._hconsole = ctypes.windll.kernel32.GetStdHandle(-12)  # STD_ERROR_HANDLE
      self._info = _CONSOLE_SCREEN_BUFFER_INFO()
      self._lib = ctypes.windll.kernel32
    else:
      self._hconsole is None

  def update(self):
    self._lib.GetConsoleScreenBufferInfo(self._hconsole, ctypes.byref(self._info))

  @property
  def screen_size(self):
    if self._hconsole is None:
      return (0, 0)
    win = self._info.srWindow
    return (win.right - win.left + 1, win.bottom - win.top + 1)

  @property
  def screen_offset(self):
    if self._hconsole is None:
      return (0, 0)
    win = self._info.srWindow
    return win.left, win.top

  @property
  def buffer_size(self):
    if self._hconsole is None:
      return (0, 0)
    size = self._info.dwSize
    return size.x, size.y

  @property
  def location(self):
    if self._hconsole is None:
      return (0, 0)
    pos = self._info.dwCursorPosition
    win = self._info.srWindow
    return pos.x - win.left, pos.y - win.top

  @property
  def location_in_buffer(self):
    if self._hconsole is None:
      return (0, 0)
    pos = self._info.dwCursorPosition
    return pos.x, pos.y

  @property
  def isatty(self):
    return self._hconsole is not None

  def move(self, x=None, y=None, *, _relative=True):
    if self._hconsole is None:
      return
    if x is None:
      if y is None:
        return
      x = self.location[0]
    elif y is None:
      y = self.location[1]
    if _relative:
      win = self._info.srWindow
      x += win.left
      y += win.top
    pos = _COORD(x, y)
    self._lib.SetConsoleCursorPosition(self._hconsole, pos)

  def move_in_buffer(self, x=None, y=None):
    self.move(x, y, _relative=False)


## Exports ##
#############

if blessed:
  module.exports = BlessedConsole()
elif os.name == 'nt':
  module.exports = WindowsConsole()
else:
  raise EnvironmentError("no console implementation found")
