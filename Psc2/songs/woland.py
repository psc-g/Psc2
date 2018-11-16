"""Woland song logic."""

from Psc2.songs import song
from Psc2.modes import bass_doubler
from Psc2.modes import looper
from Psc2.modes import mlsplainer

class Woland(song.Song):
  """This defines the logic for Woland.

  For most of the song it is in bass-doubling mode, except for the solo section
  where we use the MLSplainer mode.
  
  """

  def __init__(self, client):
    """Initialize the Woland Song.

    Args:
      client: OSCClient, used to send messages for playback.
    """
    self.eighth_note_duration = 0.5
    self.avg_velocity = 60
    self.modes = {
        'doubler': bass_doubler.BassDoubler(client, highest_bass_note=51),
        'looper': looper.Looper(
          client,
          [[(42, 4, 3), (42, 4, 3), (46, 3, 2), (46, 3, 2),  # B
            (45, 3, 2), (50, 3, 2), (40, 2, 2), (44, 2, 2), (43, 2, 2)],
           [(55, 4, 3), (55, 4, 3), (50, 3, 2), (50, 3, 2),  # C
            (49, 4, 3), (49, 4, 3), (45, 3, 2), (45, 3, 2),
            (48, 4, 3), (48, 4, 3), (46, 3, 2), (46, 3, 2),
            (53, 8, 7), (50, 8, 7)],
           [(55, 6, 5), (50, 8, 7), (49, 4, 3), (48, 4, 3),  # E
            (48, 6, 5), (47, 8, 7), (46, 4, 3), (45, 4, 3)],
           [(55, 4, 3), (55, 4, 3), (50, 3, 2), (50, 3, 2),  # C
            (49, 4, 3), (49, 4, 3), (45, 3, 2), (45, 3, 2),
            (48, 4, 3), (48, 4, 3), (46, 3, 2), (46, 3, 2),
            (53, 8, 7), (50, 8, 7)],
           [(55, 6, 5), (50, 8, 7), (49, 4, 3), (48, 4, 3),  # E
            (48, 6, 5), (47, 8, 7), (46, 4, 3), (45, 4, 3)],
          ],
          eigths_per_tap=4,
          eigth_duration=0.125),
        'doubler2': bass_doubler.BassDoubler(client, highest_bass_note=51),
        'solo': mlsplainer.MLSplainer(client)
    }
    # These allow us to go in and out of the first loop for the differen parts.
    self.looper_play = [False, True, False]
    self.looper_pos = 0
    self.current_mode = 'doubler'
    self.modes_to_process = ['doubler']
    self.tempo_set = False
    self.ready_for_solo = False

  def process_note(self, pitch, velocity, time):
    if (self.current_mode == 'looper' and
        not self.modes['looper'].playing and
        self.ready_for_solo):
      self.current_mode = 'doubler2'
      self.modes_to_process = ['doubler2']
    for mode in self.modes_to_process:
      self.modes[mode].process_note(pitch, velocity)

  def process_note_off(self, pitch, velocity, time):
    for mode in self.modes_to_process:
      self.modes[mode].process_note_off(pitch, velocity)

  def process_program(self, program):
    """Process program hits (footpedal)."""
    if self.current_mode == 'doubler2':
      self.current_mode = 'solo'
      self.modes_to_process = ['solo']
    elif self.current_mode == 'looper':
      if self.looper_pos < len(self.looper_play):
        if self.looper_play[self.looper_pos]:
          self.modes['looper'].loop_num = 0
          self.modes['looper'].start_looper_thread()
        else:
          self.modes['looper'].loop_num = 99
        self.looper_pos += 1
      elif self.modes['looper'].loop_num == 99:
        self.modes['looper'].loop_num = 1
        self.modes['looper'].start_looper_thread()
        self.ready_for_solo = True
      else:
        self.modes['looper'].increment_loop()
    elif self.current_mode == 'solo':
      self.modes['solo'].reset()
      self.modes_to_process = ['doubler']
    else:
      self.modes_to_process = []
      self.current_mode = 'looper'
      self.modes['looper'].start_looper_thread()
