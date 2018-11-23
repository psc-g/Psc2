"""AllBass song logic."""

from Psc2.songs import song
from Psc2.modes import bass_doubler

class AllBass(song.Song):
  """This defines the logic for AllBass, which is only bass doubling.
  """

  def __init__(self, client, highest_note=51):
    """Initialize the AllBass Song.

    Args:
      client: OSCClient, used to send messages for playback.
      highest_note: int, highest bass note.
    """
    self.avg_velocity = 60
    self.mode = bass_doubler.BassDoubler(client, highest_bass_note=highest_note)

  def process_note(self, pitch, velocity, time):
    self.mode.process_note(pitch, velocity)

  def process_note_off(self, pitch, velocity, time):
    self.mode.process_note_off(pitch, velocity)
