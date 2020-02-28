"""Setup for Keyboard."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app

import collections
import importlib
import os
import OSC
import threading
import time

importlib.import_module('arturiamap')
import arturiamap


MIN_MIDI = 48
MAX_MIDI = 72
WHITE_CHAR = ' '
BLACK_CHAR = '#'
PLAYING_CHAR = '*'
SEPARATOR_CHAR = '|'
BOTTOM_CHAR = '_'
# Key dimensions.
WHITE_WIDTH = 5
WHITE_HEIGHT = 6
BLACK_WIDTH = 3
BLACK_HEIGHT = 4
TOP_SIDE_WHITE_WIDTH = WHITE_WIDTH - (BLACK_WIDTH - 1) // 2
TOP_MID_WHITE_WIDTH = WHITE_WIDTH - (BLACK_WIDTH - 1)
# This specifies the configuration of keys in an octave. We assume the
# keyboard starts at C.
KEY_LAYOUTS = [
    'lw',  # C
    'b',   # C#
    'mw',  # D
    'b',   # D#
    'rw',  # E
    'lw',  # F
    'b',   # F#
    'mw',  # G
    'b',   # G#
    'mw',  # A
    'b',   # A#
    'rw'  # B
]

receive_address = ('127.0.0.1', 12345)
send_address = ('127.0.0.1', 57120)
server = OSC.OSCServer(receive_address)  # To receive from SuperCollider.

NoteSpec = collections.namedtuple('note_spec', ['midi', 'layout'])


# This dictionary maps MIDI notes to their status (on/off).
midi_key_status = {}
# This array must correspond to the keys on the actual keyboard, and is what
# will be used to draw the keyboard on-screen.
midi_keys = []


def setup_keyboard():
  i = 0
  for key in range(MIN_MIDI, MAX_MIDI + 1):
    midi_key_status[key] = False
    midi_keys.append(NoteSpec(key, KEY_LAYOUTS[i % len(KEY_LAYOUTS)]))
    i += 1


def process_note_on(addr, tags, args, source):
  global midi_keys
  midi_key_status[args[0]] = True
  draw_keyboard()

def process_note_off(addr, tags, args, source):
  global midi_keys
  midi_key_status[args[0]] = False
  draw_keyboard()

def draw_keyboard():
  """Draws the keyboard on-screen."""
  global midi_keys
  os.system('clear')
  for h in range(WHITE_HEIGHT):
    line = ''
    for key in midi_keys:
      if key.layout == 'b':
        if h < BLACK_HEIGHT:
          char_to_print = (
              PLAYING_CHAR if midi_key_status[key.midi] else BLACK_CHAR)
          line += char_to_print * BLACK_WIDTH
        continue
      char_to_print = PLAYING_CHAR if midi_key_status[key.midi] else WHITE_CHAR
      if h < BLACK_HEIGHT:
        if key.layout == 'lw':
          line += SEPARATOR_CHAR
        if key.layout == 'lw' or key.layout == 'rw':
          line += char_to_print * TOP_SIDE_WHITE_WIDTH
        else:
          line += char_to_print * TOP_MID_WHITE_WIDTH
      else:
        line += SEPARATOR_CHAR + char_to_print * WHITE_WIDTH
    line += SEPARATOR_CHAR
    print(line)
  line = ''
  for key in midi_keys:
    if key.layout == 'b':
      continue
    line += '{}{}'.format(SEPARATOR_CHAR, BOTTOM_CHAR * WHITE_WIDTH)
  line += SEPARATOR_CHAR
  print(line)


def main(_):
  setup_keyboard()
  draw_keyboard()
  # Set up and start the server.
  st = threading.Thread(target = server.serve_forever)
  st.daemon = True
  st.start()
  server.addMsgHandler('/processnoteon', process_note_on)
  server.addMsgHandler('/processnoteoff', process_note_off)

  while True:
    time.sleep(1)


if __name__ == '__main__':
  app.run(main)
