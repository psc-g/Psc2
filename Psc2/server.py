from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app

import importlib
import os
import OSC
import threading
import time

from Psc2.songs import solipair


# Global variables.
# Addresses and ports to communicate with SuperCollider.
receive_address = ('127.0.0.1', 12345)
send_address = ('127.0.0.1', 57120)
server = OSC.OSCServer(receive_address)  # To receive from SuperCollider.
client = OSC.OSCClient()  # To send to SuperCollier.
client.connect(send_address)

current_song = 'solipair'
songs = {'solipair': solipair.Solipair(client) }
local_mode = False  # If true will ask SuperCollider for soundz.


def print_status():
  print('hi there!')


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
  global songs
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
  msg = OSC.OSCMessage()
  msg.setAddress('/stopthru')
  msg.append(args)
  client.send(msg)


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


def program_event(addr, tags, args, source):
  """Events sent by the Mongoose foot controller."""
  global songs
  cc_num, _, _, _ = args
  songs['solipair'].process_program(cc_num)


def main(_):
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Turn off TF logging.
  print_status()
  
  # Set up and start the server.
  st = threading.Thread(target = server.serve_forever)
  st.start()
  server.addMsgHandler('/processnoteon', process_note_on)
  server.addMsgHandler('/processnoteoff', process_note_off)
  server.addMsgHandler('/ccevent', cc_event)
  server.addMsgHandler('/programevent', program_event)


if __name__ == '__main__':
  app.run(main)
