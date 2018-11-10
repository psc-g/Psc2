"""Solipair song logic."""

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
    self.eighth_note_duration = 0.5
    self.avg_velocity = 60
    self.modes = {
        'doubler': bass_doubler.BassDoubler(client, highest_bass_note=51),
        'solo': looper.Looper(client,
                              [(78, 1, 1), (69, 1, 1), (73, 1, 1), 
                               (78, 1, 1), (78, 1, 1), (69, 1, 1), 
                               (73, 1, 1), (77, 2, 2), (69, 1, 1), 
                               (73, 1, 1), (77, 1, 1), (77, 1, 1), 
                               (69, 1, 1), (73, 1, 1), (77, 1, 1), 
                               (76, 1, 1), (69, 1, 1), (73, 1, 1), 
                               (76, 1, 1), (76, 1, 1), (69, 1, 1), 
                               (73, 1, 1), (75, 2, 2), (69, 1, 1), 
                               (73, 1, 1), (75, 1, 1), (75, 1, 1), 
                               (69, 1, 1), (73, 1, 1), (75, 1, 1)],
                              repetitions=2,
                              playback_notes=[
                                (50, 4, 4), (50, 4, 4),
                                (49, 4, 4), (49, 4, 4),
                                (54, 4, 4), (54, 4, 4),
                                (51, 4, 4), (51, 4, 4)],
                              max_consec_mistakes=5),
    }
    self.current_mode = 'non solo'
    self.modes_to_process = ['doubler']  # Add 'solo' to auto-detect solo sect.
    self.mode_detected = None

  def process_note(self, pitch, velocity, time):
    if self.current_mode == 'solo' and not self.modes['solo'].playing:
      self.current_mode = 'non solo'
      self.modes_to_process = ['doubler']
    for mode in self.modes_to_process:
      if self.modes[mode].process_note(pitch, velocity):
        if mode == 'solo':
          self.modes_to_process = []
          self.current_mode = 'solo'

  def process_program(self, program):
    """Process program hits (footpedal)."""
    # If in 'solo' mode, any hit of the pedal will return to bass doubler mode.
    if self.current_mode == 'solo':
      self.modes['solo'].stop()
    elif program == 0:  # Tap to set tempo.
      self.modes['solo'].set_tempo()
    else:  # Start bass for solo.
      self.modes_to_process = []
      self.current_mode = 'solo'
      self.modes['solo'].start_looper_thread()
