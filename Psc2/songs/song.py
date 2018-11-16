"""Base class for a Song object."""

import abc

class Song(object):

  @abc.abstractmethod
  def process_note(self, pitch, velocity, time):
    pass

  @abc.abstractmethod
  def process_note_off(self, pitch, velocity, time):
    pass

  @abc.abstractmethod
  def process_program(self, program):
    pass
