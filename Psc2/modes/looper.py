"""A looper mode for looping over a particular section."""

import OSC
import time

from Psc2.modes import mode

class Looper(mode.Mode):
  """A Looper Mode that can 

  It is instantiated with a sequence of pitches which will be used to recognize
  when a part has been played. When this occurs, it can be queried to playback
  a particular section.
  """

  def __init__(self, ordered_notes, max_consec_mistakes=2):
    """Creates a Part object.

    Args:
      ordered_notes: list, note pitches defining a part to recognize.
      max_consec_mistakes: int, maximum number of consecutive errors allowed.
    """
    self.ordered_notes = ordered_notes
    self.curr_pos = 0
    self.max_consec_mistakes = max_consec_mistakes
    self.mistake_count = 0
    self.cumulative_times = 0.
    self.eigth_note_estimate = 0.5
    self.last_time = 0.
    self.eigths_passed = 1
    self.avg_velocity = 0.

  def proces_note(self, note, velocity):
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
      self.eigth_note_estimate = self.cumulative_times / len(self.ordered_notes)
      self.avg_velocity /= len(self.ordered_notes)
      self.curr_pos = 0
      return True
    return False

  def get_avgs(self):
    """Returns the average eigth-note length and velocity."""
    return self.eigth_note_estimate, self.avg_velocity

  def play(self, eigth_duration, velocity, client):
    """Play the stored pattern in sequence.

    Uses the specified note duration and velocity for all notes.

    Args:
      eigth_duration: float, duration of an eigth note.
      velocity: float, velocity for playback.
      client: OSCClient, used to send messages for playback.
    """
    for note, next_onset, duration in self.ordered_notes:
      msg = OSC.OSCMessage()
      msg.setAddress('/playbass')
      msg.append([note - 24, velocity])
      client.send(msg)
      time.sleep(duration * eigth_duration)
      msgoff = OSC.OSCMessage()
      msgoff.setAddress('/stopnote')
      msgoff.append([note])
      client.send(msgoff)
      if next_onset > duration:
        time.sleep((next_onset - duration) * eigth_duration)
