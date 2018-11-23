"""Espalda song logic."""

import OSC

from Psc2.songs import song
from Psc2.modes import bass_doubler
from Psc2.modes import looper

class Espalda(song.Song):
  """This defines the logic for Espalda.

  For most of the song it is in bass-doubling mode, except for the solo section
  where the bass is automated.
  
  """

  def __init__(self, client):
    """Initialize the Espalda Song.

    Args:
      client: OSCClient, used to send messages for playback.
    """
    self.client = client
    self.eighth_note_duration = 0.5
    self.avg_velocity = 60
    self.modes = {
        'doubler': bass_doubler.BassDoubler(client, highest_bass_note=54),
        'solo': looper.Looper(client,
                              [[(34, 3, 3), (46, 2, 2), (46, 2, 2), (46, 1, 1),
                                (34, 2, 2), (34, 2, 2), (46, 2, 2), (34, 2, 2)],
                               [(34, 3, 3), (46, 2, 2), (46, 2, 2), (46, 1, 1),
                                (34, 2, 2), (34, 2, 2), (46, 2, 2), (34, 2, 2),
                                (32, 3, 3), (44, 2, 2), (44, 2, 2), (44, 1, 1),
                                (32, 2, 2), (32, 2, 2), (44, 2, 2), (32, 2, 2),
                                (30, 3, 3), (42, 2, 2), (42, 2, 2), (42, 1, 1),
                                (30, 2, 2), (30, 2, 2), (42, 2, 2), (30, 2, 2),
                                (29, 3, 3), (41, 2, 2), (41, 2, 2), (41, 1, 1),
                                (27, 4, 4), (24, 4, 4)]],
                              eigths_per_tap=4)
    }
    self.current_mode = 'intro'
    self.modes_to_process = ['doubler']  # Add 'solo' to auto-detect solo sect.
    self.mode_detected = None

  def process_note(self, pitch, velocity, time):
    if self.current_mode == 'solo' and not self.modes['solo'].playing:
      self.current_mode = 'post solo'
      self.modes_to_process = ['doubler']
    for mode in self.modes_to_process:
      if self.modes[mode].process_note(pitch, velocity):
        if mode == 'solo':
          self.modes_to_process = []
          self.current_mode = 'solo'

  def process_note_off(self, pitch, velocity, time):
    for mode in self.modes_to_process:
      self.modes[mode].process_note_off(pitch, velocity)

  def process_program(self, program):
    """Process program hits (footpedal)."""
    # If in 'intro' mode, when hit set lowest bass note to G#1.
    if self.current_mode == 'intro':
      self.modes['doubler'].highest_bass_note=32
      self.current_mode = 'beethoven'
    # If in 'beethoven' mode, turn off bass doubling.
    elif self.current_mode == 'beethoven':
      self.modes['doubler'].highest_bass_note = 0
      self.current_mode = 'piano break'
    # If in 'piano break' mode, set bass limit back to original settings.
    elif self.current_mode == 'piano break':
      self.modes['doubler'].highest_bass_note = 54
      self.current_mode = 'pre solo'
    # If in 'solo' mode, any hit of the pedal will return to bass doubler mode.
    elif self.current_mode == 'solo':
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
