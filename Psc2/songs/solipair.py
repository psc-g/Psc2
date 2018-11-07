"""Solipair song logic."""

import threading

from Psc2.songs import song
from Psc2.modes import bass_doubler
from Psc2.modes import looper

class Solipair(song.Song):
  """This defines the logic for playing Solipair.

  For most of the song it is in bass-doubling mode, except for the solo section
  where the bass is automated.
  
  """

  def __init__(self, client):
    """Initialize the Solipair Song.

    Args:
      client: OSCClient, used to send messages for playback.
    """
    self.client = client
    self.playing = False
    self.eighth_note_duration = 0.5
    self.avg_velocity = 60
    self.parts = {
        'A': looper.Looper([(75, 1, 1), (70, 1, 1), (75, 1, 1), (82, 1, 1),
                        (83, 1, 1), (79, 1, 1), (80, 1, 1), (76, 1, 1),
                        (82, 1, 1), (83, 1, 1), (79, 1, 1), (80, 1, 1),
                        (75, 3, 2), (79, 2, 0.8), (74, 2, 2), (79, 1, 1),
                        (83, 3, 3), (74, 1, 1), (71, 1, 1), (74, 1, 1)]),
        'doubler': bass_doubler.BassDoubler(self.client),
        # 'Ap': looper.Looper([(75, 1, 1), (70, 1, 1), (75, 1, 1), (82, 1, 1),
        #                  (83, 1, 1), (79, 1, 1), (80, 1, 1), (76, 1, 1),
        #                  (82, 1, 1), (83, 1, 1), (79, 1, 1), (80, 1, 1),
        #                  (75, 3, 2)]),
        # 'B1': looper.Looper([(79, 2, 0.8), (74, 2, 2), (79, 1, 1),
        #                  (83, 3, 3), (83, 2, 2), (83, 3, 3), (83, 3, 3),
        #                  (78, 16, 16)]),
    }
    self.current_mode = 'doubler'

  def process_note(self, pitch, velocity, time):
    self.parts[self.current_mode].process_note(pitch, velocity)
    # if self.parts['A'].process_note(pitch, velocity):
    #   self.eigth_note_duration, self.avg_velocity = self.parts['A'].get_avgs()

  def play(self):
    """Play the song structure.
    """
    self.playing = True
    def play_song_structure():
      while True:
        if not self.playing:
          break
        self.parts['A'].play(self.eigth_note_duration, self.avg_velocity,
                             self.client)
    play_thread = threading.Thread(target = play_song_structure)
    play_thread.start()

  def stop(self):
    self.playing = False
