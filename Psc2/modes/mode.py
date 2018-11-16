"""Base class for a song mode."""

import abc

class Mode(object):

  @abc.abstractmethod
  def process_note(self, note, velocity):
    """Receive a new note to process.
    Args:
      note: int, pitch to check.
      velocity: int, possibly used for playback.
    """
    pass

  @abc.abstractmethod
  def process_note_off(self, note, velocity):
    """Receive a new note off to process.
    Args:
      note: int, pitch to check.
      velocity: int, possibly used for playback.
    """
    pass

  @abc.abstractmethod
  def get_avgs(self):
    """Returns the average eigth-note length and velocity."""
    pass

  @abc.abstractmethod
  def play(self, eigth_duration, velocity, client):
    """May play the stored pattern in sequence.

    Uses the specified note duration and velocity for all notes.

    Args:
      eigth_duration: float, duration of an eigth note.
      velocity: float, velocity for playback.
      client: OSCClient, used to send messages for playback.
    """
    pass
