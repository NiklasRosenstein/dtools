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

import progressbar  # progressbar2 Python module
import werkzeug.local
import console from './console'

# A list of currently running bars.
bars = []


class ProgressBar(progressbar.ProgressBar):
  """
  Extension of the #progressbar.ProgressBar class that works with multiple
  progressbars at the same time and offers an *indent* and *desc* parameter.

  # Parameters
  desc (str): Message to display in the progress bar.
  indent (int or str): Widget to prepend.
  """

  def __init__(self, *args, **kwargs):
    desc = kwargs.pop('desc', None)
    indent = kwargs.pop('indent', None)
    progressbar.ProgressBar.__init__(self, *args, **kwargs)

    if self.max_value is None:
      self.max_value = self._DEFAULT_MAXVAL
    if self.widgets is None:
      self.widgets = self.default_widgets()

    bar = next((w for w in self.widgets if isinstance(w, progressbar.Bar)), None)
    if bar:
      bar.marker = progressbar.widgets.create_marker('\u2593')
      bar.fill = progressbar.widgets.string_or_lambda('\u2591')
      bar.left = progressbar.widgets.string_or_lambda('')
      bar.right = progressbar.widgets.string_or_lambda('')

    # Remove the SimpleProgress and AdaptiveETA.
    self.widgets = [
      w for w in self.widgets if not isinstance(w, (
        progressbar.SimpleProgress, progressbar.AdaptiveETA))
    ]

    if desc is not None:
      self.widgets.insert(3, desc + ' ')

    if indent is not None:
      if isinstance(indent, int):
        indent = ' ' * indent
      self.widgets.insert(0, indent)

    location = console.location_in_buffer
    offset = console.screen_offset

    # FIXME: When the end of the buffer and terminal screen is reached,
    # the first ProgressBar is overwritten by the second one. We need a
    # way to figure out if we really should lift all bars by one.

    # If we're at the last line in the buffer, we have to account for
    # scrolling in the terminal window.
    if location[1] == (console.screen_size[1] - 1):
      for bar in bars:
        bar.location = (bar.location[0], bar.location[1] - 1)
    # If the Y-location of this bar matches the Y-location of the previous
    # bar, we have to offset it by one.
    elif bars and location[1] == bars[-1].location[1]:
      location = (location[0], location[1] + 1)

    self.location = location
    self.offset = offset

    # Get rid of bars that have finished.
    bars[:] = [bar for bar in bars if not bar.end_time]
    bars.append(self)

  def update(self, *args, **kwargs):
    # Update the location if the window was scrolled.
    offset = console.screen_offset
    delta = self.offset[0] - offset[0], self.offset[1] - offset[1]
    location = self.location[0] + delta[0], self.location[1] + delta[1]
    #location = self.location
    with console.movectx_in_buffer(*location):
      return progressbar.ProgressBar.update(self, *args, **kwargs)


if require.main == module:
  import time
  for i in ProgressBar(desc='MainLoop')(range(5)):
    time.sleep(0.2)
    for __ in ProgressBar(indent=2, desc='Loop {}'.format(i))(range(30)):
      time.sleep(0.01)
