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

import click
import csv
import gzip
import sys


@click.group()
def main():
  pass


@main.command()
@click.argument('directory')
@click.argument('suffix')
@click.option('--has-header/--no-header')
@click.pass_context
def join(ctx, directory, suffix, has_header):
  " Join CSV tables into one. "

  files = []
  for name in os.listdir(directory):
    if name.endswith(suffix):
      files.append(name)
  files.sort()
  if not files:
    ctx.fail('no input files')

  count = 0
  for index, name in enumerate(files):
    filename = os.path.join(directory, name)
    if name.endswith('.gz'):
      fp = gzip.open(filename)
    else:
      fp = open(filename, 'rb')
    try:
      fp = codecs.getreader('utf8')(fp)
      if has_header and index != 0:
        fp.readline()
      for line in fp:
        print(line)
    finally:
      fp.close()


@main.command()
@click.argument('file')
@click.argument('columns')
@click.pass_context
def column(ctx, file, columns):
  columns = columns.split(',')
  header = True
  try:
    columns = [int(c) for c in columns]
    header = False
  except ValueError:
    pass

  writer = csv.writer(sys.stdout)
  with open(file) as fp:
    reader = csv.reader(fp)
    if header:
      header_names = {c: i for i, c in enumerate(next(reader))}
    for row in reader:
      if not row: continue
      if header:
        new_row = [row[header_names[n]] for n in columns]
      else:
        new_row = [row[i] for i in columns]
      writer.writerow(new_row)



if require.main == module:
  main()
