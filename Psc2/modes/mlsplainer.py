"""A MLSplainer mode for hijacking human notes with machine learning ones."""

import OSC
import tensorflow as tf
import threading

import magenta
from magenta.models.melody_rnn import melody_rnn_model
from magenta.models.melody_rnn import melody_rnn_generate
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.music import sequences_lib
from magenta.protobuf import generator_pb2
from magenta.protobuf import music_pb2


from Psc2.modes import mode

class MLSplainer(mode.Mode):
  """A MLSplainer mode for hijacking human notes with machine learning ones.

  It will fill a buffer with human notes, send those over to PerformanceRNN,
  fill a buffer with machine-learning generated notes, and then hijack the
  human notes (but not the rhythm) until the buffer is empty. Then repeat.
  """

  def __init__(self,
               client,
               base_models_path='~/Psc2/magenta_models',
               model_name='attention_rnn.mag',
               min_primer_length=20,
               max_robot_length=20,
               temperature=1.0):
    tf.logging.set_verbosity(tf.logging.ERROR)
    self.client = client
    self.min_primer_length = min_primer_length
    self.max_robot_length = max_robot_length
    self.accumulated_primer_melody = []
    self.generated_melody = []
    # Mapping of notes (defaults to identity).
    self.note_mapping = {i:i for i in range(21, 109)}
    self.improv_status = 'human'  # One of 'human' or 'robot'.
    melody_model_path = '{}/{}'.format(base_models_path, model_name)
    self.melody_bundle = magenta.music.read_bundle_file(melody_model_path)
    self.temperature = temperature

  def reset(self):
    self.accumulated_primer_melody = []
    self.generated_melody = []

  def _generate_melody(self):
    melody_config_id = self.melody_bundle.generator_details.id
    melody_config = melody_rnn_model.default_configs[melody_config_id]
    generator = melody_rnn_sequence_generator.MelodyRnnSequenceGenerator(
        model=melody_rnn_model.MelodyRnnModel(melody_config),
        details=melody_config.details,
        steps_per_quarter=melody_config.steps_per_quarter,
        checkpoint=melody_rnn_generate.get_checkpoint(),
        bundle=self.melody_bundle)
    generator_options = generator_pb2.GeneratorOptions()
    generator_options.args['temperature'].float_value = self.temperature
    generator_options.args['beam_size'].int_value = 1
    generator_options.args['branch_factor'].int_value = 1
    generator_options.args['steps_per_iteration'].int_value = 1
    primer_melody = magenta.music.Melody(self.accumulated_primer_melody)
    qpm = magenta.music.DEFAULT_QUARTERS_PER_MINUTE
    primer_sequence = primer_melody.to_sequence(qpm=qpm)
    seconds_per_step = 60.0 / qpm / generator.steps_per_quarter
    # Set the start time to begin on the next step after the last note ends.
    last_end_time = (max(n.end_time for n in primer_sequence.notes)
                     if primer_sequence.notes else 0)
    melody_total_seconds = last_end_time * 3
    generate_section = generator_options.generate_sections.add(
        start_time=last_end_time + seconds_per_step,
        end_time=melody_total_seconds)
    generated_sequence = generator.generate(primer_sequence, generator_options)
    self.generated_melody = [n.pitch for n in generated_sequence.notes]
    # Get rid of primer melody.
    self.generated_melody = self.generated_melody[
        len(self.accumulated_primer_melody):]
    # Make sure generated melody is not too long.
    self.generated_melody = self.generated_melody[:self.max_robot_length]
    self.accumulated_primer_melody = []

  def _send_stopnote(self, note, velocity):
    msg = OSC.OSCMessage()
    msg.setAddress('/stopthru')
    msg.append([note, velocity])
    self.client.send(msg)

  def process_note_off(self, note, velocity):
    mapped_note = self.note_mapping[note]
    self._send_stopnote(mapped_note, velocity)
    self._send_stopnote(note, velocity)

  def _send_playnote(self, note, velocity):
    msg = OSC.OSCMessage()
    msg.setAddress('/playthru')
    msg.append([note, velocity])
    self.client.send(msg)

  def process_note(self, note, velocity):
    """Receive a new note to process.

    Args:
      note: int, pitch to check.
      velocity: int, possibly used for playback.

    Returns:
      False, no pattern to match.
    """
    if len(self.generated_melody):
      if self.improv_status != 'robot':
        self.improv_status = 'robot'
      # To avoid stuck notes, send a note off for previous mapped note.
      prev_note = self.note_mapping[note]
      self.process_note_off(prev_note, velocity)
      self.note_mapping[note] = self.generated_melody[0]
      note = self.generated_melody[0]
      self.generated_melody = self.generated_melody[1:]
    else:
      if self.improv_status != 'human':
        self.improv_status = 'human'
      self.accumulated_primer_melody.append(note)
    self._send_playnote(note, velocity)
    if len(self.accumulated_primer_melody) >= self.min_primer_length:
      magenta_thread = threading.Thread(target = self._generate_melody)
      magenta_thread.start()
