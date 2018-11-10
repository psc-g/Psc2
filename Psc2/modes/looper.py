"""A Looper mode for detecting and looping over a particular section."""

import OSC
import threading
import time

from Psc2.modes import mode

class Looper(mode.Mode):
  """A Looper Mode that can loop over a pre-defined section.

  It can operate in two modes:
  Detect:
    It is instantiated with a sequence of pitches (ordered_notes) which will be
    used to recognize when a part has been played. When the sequence has been
    recognized as complete, it will start playback of the loop.

  OnDemand:
    It will start playback of the loop upon demand. The tempo can be set via
    calls to set_tempo().
  """

  def __init__(self,
               client,
               ordered_notes,
               repetitions=1,
               playback_notes=None,
               max_consec_mistakes=2,
               eigths_per_tap=2):
    """Creates a Looper object.

    Args:
      client: OSCClient, used to send messages for playback.
      ordered_notes: list of tuples, tuples containing note pitches, number of
        eigth notes until next onset, and note duration, defining a part to
        recognize.
      repetitions: int, number of repetitions expected.
      playback_notes: list of tuples, same as ordered_notes, but defines the
        notes to playback. If None, will playback ordered_notes.
      max_consec_mistakes: int, maximum number of consecutive errors allowed.
      eigths_per_tap: int, the number of eigth notes per tap for setting tempo.
    """
    self.ordered_notes = ordered_notes
    self.client = client
    self.repetitions_needed = repetitions
    self.repetitions_passed = 0
    self.playback_notes = (ordered_notes if playback_notes is None
                           else playback_notes)
    self.curr_pos = 0
    self.max_consec_mistakes = max_consec_mistakes
    self.eigths_per_tap = eigths_per_tap
    self.mistake_count = 0
    self.cumulative_times = 0.
    self.eigth_duration = 0.5
    self.last_time = 0.
    self.eigths_passed = 1
    self.avg_velocity = 60.
    self.playing = False
    self.terminate_loop = False

  def process_note(self, note, velocity):
    """Receive a new note to check against expected pattern.

    Args:
      note: int, pitch to check.
      velocity: int, used for playback.

    Returns:
      bool indicating whether pattern has been met.
    """
    if self.curr_pos < len(self.ordered_notes):
      if self.ordered_notes[self.curr_pos][0] != note:
        if self.mistake_count < self.max_consec_mistakes:
          self.mistake_count += 1
          self.curr_pos += 1
        else:
          self.curr_pos = 0
          self.mistake_count = 0
          return False
    curr_time = time.time()
    if self.curr_pos == 0:
      self.cumulative_times = 0.
      self.avg_velocity = 0.
    else:
      self.cumulative_times += (curr_time - self.last_time) / self.eigths_passed
    self.last_time = curr_time
    self.eigths_passed = self.ordered_notes[self.curr_pos][1]
    self.avg_velocity += velocity
    self.curr_pos += 1
    if self.curr_pos == len(self.ordered_notes):
      self.repetitions_passed += 1
      if self.repetitions_passed == self.repetitions_needed:
        self.eigth_duration = self.cumulative_times / len(self.ordered_notes)
        self.avg_velocity /= len(self.ordered_notes)
        self.curr_pos = 0
        # Wait until the last note is done before starting thread.
        time.sleep(self.eigth_duration * self.ordered_notes[-1][1])
        self.start_looper_thread()
        return True
      else:
        self.curr_pos = 0
    return False

  def start_looper_thread(self):
    """Start playing back the loop in a separate thread."""
    def play_loop():
      while True:
        if self.terminate_loop:
          self.playing = False
          self.terminate_loop = False
          break
        self.play()
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

  def stop(self):
    self.terminate_loop = True

  def play(self):
    """Play the stored pattern in sequence.

    Uses the average note duration and velocity for all notes.
    """
    for note, next_onset, duration in self.playback_notes:
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
