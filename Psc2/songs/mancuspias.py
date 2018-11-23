"""Mancuspias song logic."""

from Psc2.songs import song
from Psc2.modes import bass_doubler
from Psc2.modes import looper
from Psc2.modes import mlsplainer

class Mancuspias(song.Song):
  """This defines the logic for Mancuspias.

  For most of the song it is in bass-doubling mode, except for the solo section
  where the bass is automated.
  
  """

  def __init__(self, client):
    """Initialize the Mancuspias Song.

    Args:
      client: OSCClient, used to send messages for playback.
    """
    self.eighth_note_duration = 0.5
    self.avg_velocity = 60
    self.modes = {
        'doubler': bass_doubler.BassDoubler(client, highest_bass_note=57),
        'looper': looper.Looper(
           client,
           [[(49, 2, 2), (49, 4, 2), (49, 4, 2), (49, 2, 2), (49, 20, 2),
             (45, 2, 2), (45, 4, 2), (45, 4, 2), (45, 2, 2), (45, 20, 2),
             (49, 2, 2), (49, 4, 2), (49, 4, 2), (49, 2, 2), (49, 20, 2),
             (45, 2, 2), (45, 4, 2), (45, 4, 2), (45, 2, 2), (45, 20, 2),
             (44, 2, 2), (44, 4, 2), (44, 4, 2), (44, 2, 2), (44, 20, 2),
             (46, 2, 2), (46, 4, 2), (46, 4, 2), (46, 2, 2), (46, 20, 2),
             (42, 2, 2), (42, 4, 2), (42, 4, 2), (42, 2, 2), (42, 20, 2),
             (44, 2, 2), (44, 4, 2), (44, 4, 2), (44, 2, 2), (44, 20, 2)],
            [# Dbmaj7
             (49, 3, 3), (56, 2, 2), (56, 2, 2), (56, 1, 1),
             (49, 2, 2), (49, 2, 2), (56, 5, 4),
             (49, 1, 1), (49, 1, 1), (56, 2, 2), (56, 2, 2), (56, 2, 2),
             (56, 1, 1), (49, 1, 1), (49, 1, 1), (56, 1, 1), (49, 5, 4),
             # Am7(b6)
             (48, 2, 2), (57, 1, 1), (48, 3, 1),
             (48, 2, 2), (57, 1, 1), (48, 3, 1), (57, 4, 4),
             (48, 1, 1), (48, 3, 1), (57, 1, 1), (57, 5, 1),
             (48, 1, 1), (48, 1, 1), (57, 2, 2),
             # Dbmaj7
             (49, 3, 3), (56, 2, 2), (56, 2, 2), (56, 1, 1),
             (49, 2, 2), (49, 2, 2), (56, 5, 4),
             (49, 1, 1), (49, 1, 1), (56, 2, 2), (56, 2, 2), (56, 2, 2),
             (56, 1, 1), (49, 1, 1), (49, 1, 1), (56, 1, 1), (49, 5, 4),
             # Am7(b6)
             (48, 2, 2), (57, 1, 1), (48, 3, 1),
             (48, 2, 2), (57, 1, 1), (48, 3, 1), (57, 4, 4),
             (48, 1, 1), (48, 3, 1), (57, 1, 1), (57, 5, 1),
             (48, 1, 1), (48, 1, 1), (57, 2, 2),
             # Ab6
             (48, 3, 3), (56, 2, 2), (56, 2, 2), (56, 1, 1),
             (48, 2, 2), (48, 2, 2), (56, 5, 4),
             (48, 1, 1), (48, 1, 1), (56, 2, 2), (56, 2, 2), (56, 2, 2),
             (56, 1, 1), (48, 1, 1), (48, 1, 1), (56, 1, 1), (48, 5, 4),
             # Bbsus9
             (53, 2, 2), (58, 1, 1), (53, 3, 1),
             (53, 2, 2), (58, 1, 1), (53, 3, 1), (58, 4, 4),
             (53, 1, 1), (53, 3, 1), (58, 1, 1), (58, 5, 1),
             (53, 1, 1), (53, 1, 1), (58, 2, 2),
             # Gbmaj(#4)
             (54, 3, 3), (58, 2, 2), (58, 2, 2), (58, 1, 1),
             (54, 2, 2), (54, 2, 2), (58, 5, 4),
             (54, 1, 1), (54, 1, 1), (58, 2, 2), (58, 2, 2), (58, 2, 2),
             (58, 1, 1), (54, 1, 1), (54, 1, 1), (58, 1, 1), (54, 5, 4),
             # Ab6
             (56, 2, 2), (60, 1, 1), (56, 3, 1),
             (56, 2, 2), (60, 1, 1), (56, 3, 1), (60, 4, 4),
             (56, 1, 1), (56, 3, 1), (60, 1, 1), (60, 5, 1),
             (56, 1, 1), (56, 1, 1), (60, 2, 2)]],
             eigths_per_tap=4),
        'solo': mlsplainer.MLSplainer(client)
    }
    self.current_mode = None
    self.modes_to_process = []
    self.solo_passed = False

  def process_note(self, pitch, velocity, time):
    if self.current_mode == 'looper' and not self.modes['looper'].playing:
      self.current_mode = 'doubler'
      self.modes_to_process = ['doubler']
    for mode in self.modes_to_process:
      self.modes[mode].process_note(pitch, velocity)

  def process_note_off(self, pitch, velocity, time):
    for mode in self.modes_to_process:
      self.modes[mode].process_note_off(pitch, velocity)

  def process_program(self, program):
    """Process program hits (footpedal)."""
    # If in 'solo' mode, any hit of the pedal will return to bass doubler mode.
    if self.current_mode == 'looper':
      self.modes['looper'].increment_loop()
    elif self.current_mode == 'doubler':
      if not self.solo_passed:
        self.current_mode = 'solo'
        self.modes_to_process = ['solo']
      else:
        self.current_mode = None
        self.modes_to_process = []
    elif self.current_mode == 'solo':
      self.current_mode = 'doubler'
      self.modes_to_process = ['doubler']
      self.solo_passed = True
    elif program == 0:  # Tap to set tempo.
      self.modes['looper'].set_tempo()
    else:  # Start bass for solo.
      self.modes_to_process = []
      self.current_mode = 'looper'
      self.modes['looper'].start_looper_thread()
