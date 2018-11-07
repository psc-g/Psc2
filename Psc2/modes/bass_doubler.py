"""A BassDoubler mode for doubling bass notes played."""

import OSC
import time

from Psc2.modes import mode

class BassDoubler(mode.Mode):
  """A BassDoubler mode that doubles the lowest note played."""

  def __init__(self,
               client,
               highest_bass_note=None,
               note_decay=0.1,
               max_sustain_delta=0.1,
               min_delta_sustain_off=0.1,
               min_delay_trigger=1.0):
    """Creates a BassDoubler mode.

    Args:
      client: OSCClient, used to send messages for playback.
      highest_bass_note: int, highest bass note, F#3 by default. If None, there
        are no limits on what can be doubled.
      note_decay: float, seconds before we allow bass note to change.
      max_sustain_delta: float, maximum amount of time that we allow for a
        "delayed sustain note shift" (i.e. bass note is changed, then
        immediately you lift the sustain pedal and re-press). This is very
        specific to my style of playing; I've always used this technique for a
        more smooth transition between bass notes.
      min_delta_sustain_off: float, Minimum amount of time that has to pass
        before a sustain-lift triggers a note off.
      min_delay_trigger: float, Minimum time delay between successive trigger
        events.
    """
    self.client = client
    self.concurrent_notes = []  # Keep track of all concurrently playing notes.
    self.bass_note_playing = None  # The bass note currently being played.
    self.bass_key_pressed = False  # Whether bass key is currently pressed.
    self.sustain_on = False  # Whether sustain pedal is pressed.
    self.sustain_disabled = False  # Whether to disable sustain for bass.
    self.sustain_position = 0  # Position of sustain pedal.
    self.last_sustain_onset = 0.0  # Last time when sustain was pressed.
    self.started_delayed_sustain = False  # Whether we've started a "delayed
                                          # sustain note shift"
    self.last_bass_hit = 0.0  # Time of last bass hit.
    self.last_trigger = 0.0  # Time of last trigger event.
    self.highest_bass_note = highest_bass_note
    self.note_decay = note_decay
    self.max_sustain_delta = max_sustain_delta
    self.min_delta_sustain_off = min_delta_sustain_off
    self.min_delay_trigger = min_delay_trigger

  def _send_playnote(self):
    if not self.concurrent_notes:
      return
    self.bass_note_playing = min(self.concurrent_notes)
    self.last_bass_hit = time.time()
    self.concurrent_notes = []
    self.bass_key_pressed = True
    msg = OSC.OSCMessage()
    msg.setAddress('/playbass')
    msg.append(self.bass_note_playing)
    self.client.send(msg)

  def _send_stopnote(self):
    msg = OSC.OSCMessage()
    msg.setAddress('/stopnote')
    msg.append(self.bass_note_playing)
    self.client.send(msg)
    self.bass_note_playing = None

  def process_note(self, note, velocity):
    """Receive a new note to process.

    Args:
      note: int, pitch to check.
      velocity: int, possibly used for playback.
    """
    if self.highest_bass_note is not None and note > self.highest_bass_note:
      return
    if self.bass_note_playing is not None:
      curr_time = time.time()
      elapsed_time = curr_time - self.last_bass_hit
      if (note > self.bass_note_playing[0] and
          (elapsed_time < self.note_decay or self.sustain_on)):
        if elapsed_time >= self.note_decay and self.sustain_on:
          self.last_sustain_onset = time.time()
          self.concurrent_notes.append(args)
        return
      self._send_stopnote()
    self.concurrent_notes.append([note, velocity])
    self._send_playnote()

  def play(self, eigth_duration, velocity, client):
    pass
