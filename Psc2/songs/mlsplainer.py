"""MLSplainer song logic."""

from Psc2.songs import song
from Psc2.modes import mlsplainer

class MLSplainer(song.Song):
  """This defines the logic for MLSplainer, which is only bass doubling.
  """

  def __init__(self, client):
    """Initialize the MLSplainer Song.

    Args:
      client: OSCClient, used to send messages for playback.
    """
    self.avg_velocity = 60
    self.mode = mlsplainer.MLSplainer(client, print_ascii_arts=True)
    self.mlsplain = True

  def process_note(self, pitch, velocity, time):
    if self.mlsplain:
      self.mode.process_note(pitch, velocity)

  def process_note_off(self, pitch, velocity, time):
    if self.mlsplain:
      self.mode.process_note_off(pitch, velocity)

  def process_program(self, program):
    """Turn bass doubling on/off."""
    self.mlsplain = not self.mlsplain
