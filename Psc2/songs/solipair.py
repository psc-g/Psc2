"""Solipair song logic."""

import OSC

from Psc2.songs import song
from Psc2.modes import bass_doubler
from Psc2.modes import looper

class Solipair(song.Song):
  """This defines the logic for Solipair.

  For most of the song it is in bass-doubling mode, except for the solo section
  where the bass is automated.
  
  """

  def __init__(self, client):
    """Initialize the Solipair Song.

    Args:
      client: OSCClient, used to send messages for playback.
    """
    self.client = client
    self.eighth_note_duration = 0.5
    self.avg_velocity = 60
    self.modes = {
        'doubler': bass_doubler.BassDoubler(client, highest_bass_note=51),
        'solo': looper.Looper(client,
                              [[(38, 4, 4), (38, 4, 4),
                                (37, 4, 4), (37, 4, 4),
                                (42, 4, 4), (42, 4, 4),
                                (39, 4, 4), (39, 4, 4)]],
                              eigths_per_tap=4),
    }
    self.current_mode = 'non solo'
    self.modes_to_process = ['doubler']

  def process_note(self, pitch, velocity, time):
    if self.current_mode == 'solo' and not self.modes['solo'].playing:
      self.current_mode = 'non solo'
      self.modes_to_process = ['doubler']
    for mode in self.modes_to_process:
      if mode == 'doubler':
        velocity += 15
      self.modes[mode].process_note(pitch, velocity)

  def process_note_off(self, pitch, velocity, time):
    for mode in self.modes_to_process:
      self.modes[mode].process_note_off(pitch, velocity)

  def process_program(self, program):
    """Process program hits (footpedal)."""
    # If in 'solo' mode, any hit of the pedal will return to bass doubler mode.
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
