"""Bass doubler.
This is a server that communicates with SuperCollider for interacting with a
MIDI controller.

It handles all the logic for figuring out when to turn on/off the bass notes.
"""
import OSC
import threading
import time

# Global Variables
# Addresses and ports to communicate with SuperCollider.
receive_address = ('127.0.0.1', 12345)
send_address = ('127.0.0.1', 57120)
server = OSC.OSCServer(receive_address)  # To receive from SuperCollider.
client = OSC.OSCClient()  # To send to SuperCollier.
client.connect(send_address)

# Variables set during playback.
concurrent_notes = []  # To keep track of all concurrently playing notes. 
bass_note_playing = None  # The bass note currently being played.
bass_key_pressed = False  # Whether bass key is currently being pressed.
sustain_on = False  # Whether sustain pedal is pressed.
sustain_position = 0  # Position of sustain pedal.
last_sustain_onset = 0.0  # Last time when sustain was pressed.
started_delayed_sustain = False  # Whether we've started a "delayed sustain
                                 # note shift"
last_bass_hit = 0.0  # Time of last bass hit.
last_trigger = 0.0  # Time of last trigger event.

# Variables for configuring server.
highest_bass_note = 54  # F#3 by default.
listening_for_highest_bass_note = False  # To set new limit for bass notes.
octave_shift = 1  # Whether to shift pitch sent to controller by octaves.
bass_note_decay = 0.5  # Seconds before we allow bass note to change.
max_sustain_delta = 0.1  # Maximum amount of time that we allow for a
                         # "delayed sustain note shift" (i.e. bass note is
                         # changed, then immediately you lift the sustain pedal
                         # and re-press). This is very specific to my style of
                         # playing; I've always used this technique for a more
                         # smooth transition between bass notes.
min_delta_sustain_off = 0.1  # Minimum amount of time that has to pass before a
                             # sustain-lift triggers a note off.
min_delay_trigger = 1.0  # Minimum time delay between successive trigger
                         # events.
active = True  # Whether this server is active.


def send_playnote():
  """Send a `playnote` message to SuperCollider.

  This method chooses the lowest pitch from `concurrent_notes`, shifts it by
  `octave_shift`, and sends it to SuperCollider (which will redirect it to the
  MIDI controller).

  Side effects:
    - Update `last_bass_hit`
    - Clears `concurrent_notes`
    - Sets `bass_keY_pressed` to False
  """
  global bass_note_playing
  global bass_key_pressed
  global concurrent_notes
  global last_bass_hit
  if not concurrent_notes:
    return
  bass_note_playing = min(concurrent_notes)
  bass_note_playing[0] += octave_shift * 12
  msg = OSC.OSCMessage()
  msg.setAddress('/playnote')
  msg.append(bass_note_playing)
  client.send(msg)
  last_bass_hit = time.time()
  concurrent_notes = []
  bass_key_pressed = True


def send_stopnote(note):
  """Send a `stopnote` message to SuperCollider.

  Will send nothing if `bass_note_playing` is not set.
  """
  if not bass_note_playing:
    return
  msg = OSC.OSCMessage()
  msg.setAddress('/stopnote')
  msg.append(bass_note_playing)
  client.send(msg)


def process_note_on(addr, tags, args, source):
  """Handler for `/processnoteon` messages from SuperCollider.

  This will process the event of a key press on the MIDI controller, detected
  by SuperCollider. Depending on the state of the server it will do different
  things:
  - not active: ignore.
  - listening_for_highest_bass_note: will set highest_bass_note
  - note played higher than highest_bass_note: ignore
  - else if there is already a bass note playing:
    - if the current note is higher than the current bass note, enough time has
      passed, and the sustain is still on, add this note to `concurrent_notes`
    - otherwise (if the new note is lower than current bass note being played
      and enough time has passed and the sustain is not on), stop the current
      bass note from playing, add this note to `concurrent_notes`, and call
      `send_playnote()`

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global active
  global bass_note_decay
  global bass_note_playing
  global concurrent_notes
  global highest_bass_note
  global last_bass_hit
  global last_sustain_onset
  global listening_for_highest_bass_note
  global start_time
  global sustain_on
  if not active:
    return
  if listening_for_highest_bass_note:
    highest_bass_note = args[0]
    print('set highest bass note to: {}'.format(args[0]))
    listening_for_highest_bass_note = False
    return
  if args[0] > highest_bass_note:
    return
  if bass_note_playing is not None:
    curr_note = args[0] + (octave_shift * 12)
    curr_time = time.time()
    elapsed_time = curr_time - last_bass_hit
    if (curr_note > bass_note_playing[0] and
      (elapsed_time < bass_note_decay or sustain_on)):
      if elapsed_time >= bass_note_decay and sustain_on:
        last_sustain_onset = time.time()
        concurrent_notes.append(args)
      return
    send_stopnote(bass_note_playing)
    bass_note_playing = None
  concurrent_notes.append(args)
  send_playnote()


def process_note_off(addr, tags, args, source):
  """Handler for `/processnoteoff` messages from SuperCollider.

  - If the note depressed is the current bass note being played, set
    `bass_key_pressed` to False to indicate that they key is no longer being
    pressed.
  - If server not active or no bass is playing or the current depressed note is
    not the bass note being played, or the sustain is on, ignore.
  - Otherwise, if the note depressed is the current bass note being played, set
    `bass_key_pressed` to False, stop the note from playing.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global bass_note_playing
  global bass_key_pressed
  global sustain_on
  curr_note = args[0] + (octave_shift * 12)
  if bass_note_playing is not None and curr_note == bass_note_playing[0]:
    bass_key_pressed = False
  if (not active or
    bass_note_playing is None or
    curr_note != bass_note_playing[0] or
    sustain_on):
    return
  send_stopnote(bass_note_playing)
  bass_note_playing = None


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
  global bass_note_playing
  global bass_key_pressed
  global last_bass_hit
  global last_sustain_onset
  global max_sustain_delta
  global min_delta_sustain_off
  global started_delayed_sustain
  global sustain_on
  global sustain_position
  if not args:
    return
  # Logic to deal with the sustain pedal.
  if args[0] == 64:  # 64 is on my keyboard, probably not universal.
    elapsed_time = time.time() - last_sustain_onset
    if (sustain_position > args[1] and elapsed_time < max_sustain_delta and
        not started_delayed_sustain and not bass_key_pressed):
      send_stopnote(bass_note_playing)
      bass_note_playing = None
      send_playnote()
      started_delayed_sustain = True
    sustain_position = args[1]
    new_sustain_on = sustain_position > 0
    if sustain_on and not new_sustain_on:
      curr_time = time.time()
      if (curr_time - last_bass_hit > min_delta_sustain_off and
          not started_delayed_sustain and not bass_key_pressed):
        send_stopnote(bass_note_playing)
    if not sustain_on and new_sustain_on and started_delayed_sustain:
      started_delayed_sustain = False
    sustain_on = new_sustain_on


def set_highest_bass_note(addr, tags, args, source):
  """Handler for `/sethighestbassnote` messages from SuperCollider.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global highest_bass_note
  highest_bass_note = args[0]
  print('set highest bass note to: {}'.format(args[0]))

def set_octave_shift(addr, tags, args, source):
  """Handler for `/setoctaveshift` messages from SuperCollider.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global octave_shift
  octave_shift = args[0]
  print('set octave shift to: {}'.format(args[0]))


def set_bass_note_decay(addr, tags, args, source):
  """Handler for `/setbassnotedecay` messages from SuperCollider.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global bass_note_decay
  bass_note_decay = args[0]
  print('set bass note decay to: {}'.format(args[0]))


def bend_event(addr, tags, args, source):
  """Handler for `/setbendevent` messages from SuperCollider.

  If the bend stick is moved (and kept) to the left, we can hit a key to set
  the highest bass note.
  Moving the stick to the right triggers the server on/off.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global active
  global last_trigger
  global listening_for_highest_bass_note
  global min_delay_trigger
  if args and args[0] < 8192:  # 8192 is center position on my keyboard.
    listening_for_highest_bass_note = True
    return
  elif args and args[0] == 8192:
    listening_for_highest_bass_note = False
    return
  curr_time = time.time()
  if (curr_time - last_trigger) < min_delay_trigger:
    return
  active = not active
  print('set active to {}'.format(active))
  last_trigger = curr_time


# Print default setup.
print('starting server with:')
print('\tactive: {}'.format(active))
print('\thighest bass note: {}'.format(highest_bass_note))
print('\toctave shift: {}'.format(octave_shift))
print('\tbass note decay: {}'.format(bass_note_decay))

# Set up and start the server.
st = threading.Thread(target = server.serve_forever)
st.start()
server.addMsgHandler('/processnoteon', process_note_on)
server.addMsgHandler('/processnoteoff', process_note_off)
server.addMsgHandler('/sethighestbassnote', set_highest_bass_note)
server.addMsgHandler('/setoctaveshift', set_octave_shift)
server.addMsgHandler('/setbassnotedecay', set_bass_note_decay)
server.addMsgHandler('/bendevent', bend_event)
server.addMsgHandler('/ccevent', cc_event)
