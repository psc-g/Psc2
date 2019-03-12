from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app

import importlib
import os
import OSC
import threading
import time

from Psc2.songs import allbass
from Psc2.songs import claudius_irae
from Psc2.songs import espalda
from Psc2.songs import mancuspias
from Psc2.songs import mlsplainer
from Psc2.songs import solipair
from Psc2.songs import woland


# Global variables.
# Addresses and ports to communicate with SuperCollider.
receive_address = ('127.0.0.1', 12345)
send_address = ('127.0.0.1', 57120)
server = OSC.OSCServer(receive_address)  # To receive from SuperCollider.
client = OSC.OSCClient()  # To send to SuperCollier.
client.connect(send_address)

current_song = 'ms'
songs = {
    'ab': allbass.AllBass(client),
    'ci': claudius_irae.ClaudiusIrae(client),
    'es': espalda.Espalda(client),
    'ma': mancuspias.Mancuspias(client),
    'ms': mlsplainer.MLSplainer(client),
    'no': None,
    'so': solipair.Solipair(client),
    'wo': woland.Woland(client),
}
local_mode = False  # If true will ask SuperCollider for soundz.


def print_status():
  print('CURRENT SONG: ' + type(songs[current_song]).__name__)


def process_note_on(addr, tags, args, source):
  """Handler for `/processnoteon` messages from SuperCollider.

  This will process the event of a key press on the MIDI controller, detected
  by SuperCollider.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global local_mode
  global current_song
  global songs
  if current_song == 'no':
    return
  songs[current_song].process_note(args[0], args[1], 0)
  if local_mode:
    msg = OSC.OSCMessage()
    msg.setAddress('/playwurly')
    msg.append(args)
    client.send(msg)


def process_note_off(addr, tags, args, source):
  """Handler for `/processnoteoff` messages from SuperCollider.

  - If the note depressed is the current bass note being played, set
    `bass_key_pressed` to False to indicate that they key is no longer being
    pressed.
  - If server mode == 'disabled' or no bass is playing or the current depressed
    note is not the bass note being played, or the sustain is on, ignore.
  - Otherwise, if the note depressed is the current bass note being played, set
    `bass_key_pressed` to False, stop the note from playing.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global current_song
  global songs
  if current_song == 'no':
    return
  songs[current_song].process_note_off(args[0], args[1], 0)


def cc_event(addr, tags, args, source):
  """Handler for `/ccevent` messages from SuperCollider.

  Logic for dealing with sustain pedal, especially the delayed sustain note
  shift mentioned above. Specifically, detect when the sustain is being lifted
  but a new note has recently been played. If not much time passes and the
  pedal is released then repressed quickly, this will indicate a "delayed
  sustain note shift". Note that this means there is a small lag between when
  the new note is hit and when it actually sounds. This is usually not
  perceptible when other notes are playing, but can be perceptible otherwise. I
  need to play around with this to improve the logic.

  Otherwise , just deal with the sustain pedal like it's normally used.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  # cc_num, cc_chan, cc_src, cc_args = args
  pass


def change_song(addr, tags, args, source):
  """Handler for `/changesong` messages from SuperCollider.

  Prints a prompt to change song being played.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global current_song
  global songs
  if args[0] == 0:
    print('current song: {}'.format(current_song))
    while True:
      print('choose new song:')
      for song in songs.keys():
        print('\t{} ({})'.format(song, type(songs[song]).__name__))
      new_song = raw_input('new song: ')
      if new_song in songs.keys():
        msg = OSC.OSCMessage()
        msg.setAddress('/reset')
        msg.append(args)
        client.send(msg)
        current_song = new_song
        print_status()
        break
      print('invalid song, try again...')


def program_event(addr, tags, args, source):
  """Events sent by the Mongoose foot controller."""
  global current_song
  global songs
  if current_song == 'no':
    return
  cc_num, _, _, _ = args
  songs[current_song].process_program(cc_num)


def main(_):
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Turn off TF logging.
  print_status()

  # Set up and start the server.
  st = threading.Thread(target = server.serve_forever)
  st.daemon = True
  st.start()
  server.addMsgHandler('/processnoteon', process_note_on)
  server.addMsgHandler('/processnoteoff', process_note_off)
  server.addMsgHandler('/ccevent', cc_event)
  server.addMsgHandler('/programevent', program_event)
  server.addMsgHandler('/changesong', change_song)

  while True:
    time.sleep(1)


if __name__ == '__main__':
  app.run(main)
