"""ClaudiusIrae song logic."""

import OSC

from Psc2.songs import song
from Psc2.modes import bass_doubler
from Psc2.modes import looper

class ClaudiusIrae(song.Song):
  """This defines the logic for ClaudiusIrae.

  For most of the song it is in bass-doubling mode, except for the solo section
  where the bass is automated.
  
  """

  def __init__(self, client):
    """Initialize the ClaudiusIrae Song.

    Args:
      client: OSCClient, used to send messages for playback.
    """
    self.client = client
    self.eighth_note_duration = 0.5
    self.avg_velocity = 60
    self.modes = {
        'doubler': bass_doubler.BassDoubler(client, highest_bass_note=54),
        'solo': looper.Looper(client,
                              [[(45, 5, 5), (52, 3, 3), (50, 5, 5), (57, 3, 3),
                                (52, 5, 5), (59, 3, 3), (61, 5, 5), (57, 3, 3),
                                (50, 5, 5), (57, 3, 3), (53, 5, 5), (57, 3, 3),
                                (56, 5, 5), (52, 3, 3), (49, 5, 5), (52, 3, 3)
                              ]],
                              eigths_per_tap=4)
    }
    self.current_mode = 'doubler'
    self.modes_to_process = ['doubler']  # Add 'solo' to auto-detect solo sect.
    self.mode_detected = None

  def process_note(self, pitch, velocity, time):
    if self.current_mode == 'solo' and not self.modes['solo'].playing:
      self.current_mode = 'post solo'
      self.modes_to_process = ['doubler']
    for mode in self.modes_to_process:
      self.modes[mode].process_note(pitch, velocity)

  def process_note_off(self, pitch, velocity, time):
    for mode in self.modes_to_process:
      self.modes[mode].process_note_off(pitch, velocity)

  def process_program(self, program):
    """Process program hits (footpedal)."""
    if self.current_mode == 'solo':
      self.modes['solo'].increment_loop()
    elif program == 0:  # Tap to set tempo.
      self.modes['solo'].set_tempo()
    else:  # Start bass for solo.
      msg = OSC.OSCMessage()
      msg.setAddress('/allnotesoff')
      self.client.send(msg)
      self.modes_to_process = []
      self.current_mode = 'solo'
      self.modes['solo'].start_looper_thread()
