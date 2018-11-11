"""A Looper mode for detecting and looping over a particular section."""

import OSC
import threading
import time

from Psc2.modes import mode

class Looper(mode.Mode):
  """A Looper Mode that can loop over a set of pre-defined sections.

  It will start playback of the loop upon demand. The tempo can be set via
  calls to set_tempo().
  """

  def __init__(self,
               client,
               playback_notes,
               eigths_per_tap=2,
               stop_midi_in=True):
    """Creates a Looper object.

    Args:
      client: OSCClient, used to send messages for playback.
      playback_notes: list of list of tuples, tuples containing note pitches,
        number of eigth notes until next onset, and note duration, defining a
        part to be looped over.
      eigths_per_tap: int, the number of eigth notes per tap for setting tempo.
      stop_midi_in: bool, when True will stop receiving MIDI notes when looper
        is active.
    """
    self.client = client
    self.repetitions_passed = 0
    self.playback_notes = playback_notes
    self.curr_pos = 0
    self.eigths_per_tap = eigths_per_tap
    self.mistake_count = 0
    self.cumulative_times = 0.
    self.eigth_duration = 0.5
    self.last_time = 0.
    self.eigths_passed = 1
    self.avg_velocity = 60.
    self.playing = False
    self.loop_num = 0
    self.stop_midi_in = stop_midi_in

  def start_looper_thread(self):
    """Start playing back the loop in a separate thread."""
    def play_loop():
      while True:
        if self.loop_num >= len(self.playback_notes):
          self.playing = False
          self.terminate_loop = False
          if self.stop_midi_in:
            msg = OSC.OSCMessage()
            msg.setAddress('/togglethru')
            self.client.send(msg)
          break
        self.play()
    if self.stop_midi_in:
      msg = OSC.OSCMessage()
      msg.setAddress('/togglethru')
      self.client.send(msg)
    self.playing = True
    play_thread = threading.Thread(target = play_loop)
    play_thread.start()

  def set_tempo(self):
    """Set the tempo by tapping."""
    curr_time = time.time()
    if self.curr_pos == 0:
      self.cumulative_times = 0.
    else:
      self.cumulative_times += (
          (curr_time - self.last_time) / self.eigths_per_tap)
    self.last_time = curr_time
    self.curr_pos += 1
    # We require at least 4 taps before we're confident of tempo.
    if self.curr_pos > 4:
      self.eigth_duration = self.cumulative_times / self.curr_pos

  def increment_loop(self):
    self.loop_num += 1

  def play(self):
    """Play the stored pattern in sequence.

    Uses the average note duration and velocity for all notes.
    """
    for note, next_onset, duration in self.playback_notes[self.loop_num]:
      msg = OSC.OSCMessage()
      msg.setAddress('/playthru')
      msg.append([note, int(self.avg_velocity)])
      self.client.send(msg)
      time.sleep(duration * self.eigth_duration)
      msgoff = OSC.OSCMessage()
      msgoff.setAddress('/stopthru')
      msgoff.append([note, int(self.avg_velocity)])
      self.client.send(msgoff)
      if next_onset > duration:
        time.sleep((next_onset - duration) * self.eigth_duration)
