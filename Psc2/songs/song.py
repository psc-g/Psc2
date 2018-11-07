"""Base class for a Song object."""

import abc

class Song(object):

  @abc.abstractmethod
  def process_note(self, pitch, velocity, time):
    pass
