"""Setup for NIPS 2018 Creativity Workshop.
This is a server that communicates with SuperCollider for interacting with a
MIDI controller.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app

import collections
import importlib
import os
import OSC
from sortedcontainers import SortedList
import threading
import tensorflow as tf
import time

import magenta
from magenta.models.melody_rnn import melody_rnn_model
from magenta.models.melody_rnn import melody_rnn_generate
from magenta.models.melody_rnn import melody_rnn_sequence_generator
from magenta.models.drums_rnn import drums_rnn_model
from magenta.models.drums_rnn import drums_rnn_sequence_generator
from magenta.music import sequences_lib
from magenta.protobuf import generator_pb2
from magenta.protobuf import music_pb2

importlib.import_module('ascii_arts')
import ascii_arts
importlib.import_module('nanokontrolmap')
import nanokontrolmap

# Global Variables
# Addresses and ports to communicate with SuperCollider.
receive_address = ('127.0.0.1', 12345)
send_address = ('127.0.0.1', 57120)
server = OSC.OSCServer(receive_address)  # To receive from SuperCollider.
client = OSC.OSCClient()  # To send to SuperCollier.
client.connect(send_address)
nanokontrol_id = None

class TimeSignature:
  numerator = 7
  denominator = 8

time_signature = TimeSignature()
qpm = magenta.music.DEFAULT_QUARTERS_PER_MINUTE
num_bars = 2
num_steps = int(num_bars * time_signature.numerator * 16 / time_signature.denominator)

PlayableNote = collections.namedtuple('playable_note',
                                      ['type', 'note', 'instrument', 'onset'])
playable_notes = SortedList(key=lambda x: x.onset)

play_loop = False
seed_drum_sequence = None
last_tap_onset = None
beat_length = None
last_first_beat = 0.0  # Last time we passed the first beat during playback.
# Last first beat from the moment the bass started playing.
last_first_beat_for_record = None
bass_line = []
bass_volume = 1.0
chords_volume = 1.0
improv_volume = 1.0
MAX_TAP_DELAY = 5.0
# Robot improv specific variables.
min_primer_length = 20
max_robot_length = 20
accumulated_primer_melody = []
generated_melody = []
# Mapping of notes (defaults to identity).
note_mapping = {i:i for i in range(21, 109)}
mode = 'free'  # Mode of operation: {'free', 'bass', 'chords', 'improv'}.
improv_status = 'psc'  # One of 'psc' or 'robot'.
playable_instruments = set(['click', 'bass', 'drums', 'chords', 'stop'])

# Read in the PerformanceRNN model.
BASE_MODELS_PATH = '/home/psc/pyosc/psc2/magenta_models'
MELODY_MODEL_PATH = BASE_MODELS_PATH + '/attention_rnn.mag'
DRUMS_MODEL_PATH = BASE_MODELS_PATH + '/drum_kit_rnn.mag'
melody_bundle = magenta.music.read_bundle_file(MELODY_MODEL_PATH)
drums_bundle = magenta.music.read_bundle_file(DRUMS_MODEL_PATH)
temperature = 1.0
# Set up the mapping from pitch to drum function.
DRUM_MAPPING = {
    # bass drum
    36: 'kick', 35: 'kick',
    # snare drum
    38: 'snare', 27: 'snare', 28: 'snare', 31: 'snare', 32: 'snare',
    33: 'snare', 34: 'snare', 37: 'snare', 39: 'snare', 40: 'snare',
    56: 'snare', 65: 'snare', 66: 'snare', 75: 'snare', 85: 'snare',
    # closed hi-hat
    42: 'clhat', 44: 'clhat', 54: 'clhat', 68: 'clhat', 69: 'clhat',
    70: 'clhat', 71: 'clhat', 73: 'clhat', 78: 'clhat', 80: 'clhat',
    # open hi-hat
    46: 'ophat', 67: 'ophat', 72: 'ophat', 74: 'ophat', 79: 'ophat',
    81: 'ophat',
    # low tom
    45: 'lowtom', 29: 'lowtom', 41: 'lowtom', 61: 'lowtom', 64: 'lowtom',
    84: 'lowtom',
    # mid tom
    48: 'midtom', 47: 'midtom', 60: 'midtom', 63: 'midtom', 77: 'midtom',
    86: 'midtom', 87: 'midtom',
    # high tom
    50: 'hightom', 30: 'hightom', 43: 'hightom', 62: 'hightom',
    76: 'hightom', 83: 'hightom',
    # crash cymbal
    49: 'crash', 55: 'crash', 57: 'crash', 58: 'crash',
    # ride cymbal
    51: 'ride', 52: 'ride', 53: 'ride', 59: 'ride', 82: 'ride'
}


def generate_melody():
  """Generate a new melody by querying the model."""
  global melody_bundle
  global accumulated_primer_melody
  global generated_melody
  global max_robot_length
  melody_config_id = melody_bundle.generator_details.id
  melody_config = melody_rnn_model.default_configs[melody_config_id]
  generator = melody_rnn_sequence_generator.MelodyRnnSequenceGenerator(
      model=melody_rnn_model.MelodyRnnModel(melody_config),
      details=melody_config.details,
      steps_per_quarter=melody_config.steps_per_quarter,
      checkpoint=melody_rnn_generate.get_checkpoint(),
      bundle=melody_bundle)
  generator_options = generator_pb2.GeneratorOptions()
  generator_options.args['temperature'].float_value = 1.0
  generator_options.args['beam_size'].int_value = 1
  generator_options.args['branch_factor'].int_value = 1
  generator_options.args['steps_per_iteration'].int_value = 1
  primer_melody = magenta.music.Melody(accumulated_primer_melody)
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
  generated_melody = [n.pitch for n in generated_sequence.notes]
  # Get rid of primer melody.
  generated_melody = generated_melody[len(accumulated_primer_melody):]
  # Make sure generated melody is not too long.
  generated_melody = generated_melody[:max_robot_length]
  accumulated_primer_melody = []


def set_click():
  global num_bars
  global num_steps
  global time_signature
  global playable_notes
  # First clear previous click.
  if len(playable_notes) > 0:
    playable_notes = SortedList([x for x in playable_notes if x.type != 'click'],
                                key=lambda x: x.onset)
  num_steps = int(num_bars * time_signature.numerator * 16 / time_signature.denominator)
  step = 0
  beat = 0
  note_length = int(16 / time_signature.denominator)
  while step < num_steps:
    if step == 0:
      instrument = 'click0'
    else:
      instrument = 'click1' if beat % time_signature.numerator == 0 else 'click2'
    playable_notes.add(PlayableNote(type='click',
                                    note=[],
                                    instrument=instrument,
                                    onset=step))
    step += note_length
    beat += 1


def looper():
  global playable_notes
  global last_first_beat
  global last_first_beat_for_record
  global num_steps
  global qpm
  global mode
  global playable_instruments
  global bass_volume
  global chords_volume
  global play_loop
  local_playable_notes = None
  while True:
    if not play_loop or len(playable_notes) == 0:
      time.sleep(0.5)
      continue
    step_length = 60. / qpm / 4.0
    curr_step = 0
    # Get a local copy of playable_notes to avoid things being changed in the
    # middle of a loop.
    local_playable_notes = list(playable_notes)
    last_first_beat = time.time()
    if (last_first_beat_for_record is not None and
        last_first_beat > last_first_beat_for_record):
      last_first_beat_for_record = None
      mode = 'free'
      print_status()
    if local_playable_notes[0].onset != 0:
      curr_step = local_playable_notes[0].onset
    for playable_note in local_playable_notes:
      tts = step_length * (playable_note.onset - curr_step)
      if tts < 0:
        continue
      time.sleep(tts)
      curr_step = playable_note.onset
      if playable_note.type not in playable_instruments:
        continue
      prefix = '/stop' if playable_note.type == 'stop' else '/play'
      msg = OSC.OSCMessage()
      msg.setAddress(prefix + playable_note.instrument)
      note = list(playable_note.note)
      if playable_note.type == 'bass':
        note[1] *= bass_volume
      elif playable_note.type == 'chords':
        note[1] *= chords_volume
      msg.append(note)
      client.send(msg)
    tts = step_length * (num_steps - local_playable_notes[-1].onset)
    if tts > 0:
      time.sleep(tts)




def generate_drums():
  """Generate a new drum groove by querying the model."""
  global drums_bundle
  global generated_drums
  global playable_notes
  global seed_drum_sequence
  global num_steps
  global qpm
  global total_seconds
  global temperature
  drums_config_id = drums_bundle.generator_details.id
  drums_config = drums_rnn_model.default_configs[drums_config_id]
  generator = drums_rnn_sequence_generator.DrumsRnnSequenceGenerator(
      model=drums_rnn_model.DrumsRnnModel(drums_config),
      details=drums_config.details,
      steps_per_quarter=drums_config.steps_per_quarter,
      checkpoint=melody_rnn_generate.get_checkpoint(),
      bundle=drums_bundle)
  generator_options = generator_pb2.GeneratorOptions()
  generator_options.args['temperature'].float_value = temperature
  generator_options.args['beam_size'].int_value = 1
  generator_options.args['branch_factor'].int_value = 1
  generator_options.args['steps_per_iteration'].int_value = 1
  if seed_drum_sequence is None:
    primer_drums = magenta.music.DrumTrack([frozenset([36])])
    primer_sequence = primer_drums.to_sequence(qpm=qpm)
    local_num_steps = num_steps
  else:
    primer_sequence = seed_drum_sequence
    local_num_steps = num_steps * 2
  seconds_per_step = 60.0 / qpm / 4.0
  total_seconds = local_num_steps * seconds_per_step
  # Set the start time to begin on the next step after the last note ends.
  last_end_time = (max(n.end_time for n in primer_sequence.notes)
                   if primer_sequence.notes else 0)
  generator_options.generate_sections.add(
      start_time=last_end_time + seconds_per_step,
      end_time=total_seconds)
  generated_sequence = generator.generate(primer_sequence, generator_options)
  generated_sequence = sequences_lib.quantize_note_sequence(generated_sequence, 4)
  if seed_drum_sequence is not None:
    i = 0
    while i < len(generated_sequence.notes):
      if generated_sequence.notes[i].quantized_start_step < num_steps:
        del generated_sequence.notes[i]
      else:
        generated_sequence.notes[i].quantized_start_step -= num_steps 
        generated_sequence.notes[i].quantized_end_step -= num_steps 
        i += 1
  drum_pattern = [(n.pitch,
                   n.quantized_start_step,
                   n.quantized_end_step) for n in generated_sequence.notes]
  # First clear the last drum pattern.
  if len(playable_notes) > 0:
    playable_notes = SortedList([x for x in playable_notes if x.type != 'drums'],
                                key=lambda x: x.onset)
  for p, s, e in drum_pattern:
    playable_notes.add(PlayableNote(type='drums',
                                    note=[],
                                    instrument=DRUM_MAPPING[p],
                                    onset=s))


def send_playnote(note=None, sound='wurly'):
  """Send a `playnote` message to SuperCollider.

  Will send different commands based on the sound desired.
  """
  if note is None:
    return
  note[1] = max(1, note[1])
  msg = OSC.OSCMessage()
  command = '/play{}'.format(sound)
  msg.setAddress(command)
  msg.append(note)
  client.send(msg)


def send_stopnote(note):
  """Send a `stopnote` message to SuperCollider.
  """
  if note is None:
    return
  msg = OSC.OSCMessage()
  msg.setAddress('/stopnote')
  msg.append(note)
  client.send(msg)


def process_note_on(addr, tags, args, source):
  """Handler for `/processnoteon` messages from SuperCollider.

  This will process the event of a key press on the MIDI controller, detected
  by SuperCollider. Depending on the state of the server it will do different
  things.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global accumulated_primer_melody
  global generated_melody
  global min_primer_length
  global note_mapping
  global improv_status
  global mode
  global qpm
  global time_signature
  global start_time
  global last_first_beat
  global last_first_beat_for_record
  global bass_line
  global playable_notes
  global improv_volume
  sound = 'wurly'
  note = list(args)
  if mode == 'bass':
    sound = 'bass'
    if (last_first_beat_for_record is None or
        last_first_beat == last_first_beat_for_record):
      curr_time = time.time()
      steps_per_second = int(qpm * 4 / 60)
      curr_time_step = sequences_lib.quantize_to_step(
          curr_time - last_first_beat, steps_per_second)
      playable_notes.add(PlayableNote(type='bass',
                               note=note,
                               instrument='bass',
                               onset=curr_time_step))
      bass_line.append(PlayableNote(type='drums',
                                    note=note,
                                    instrument='bass',
                                    onset=curr_time_step))
      last_first_beat_for_record = last_first_beat
  elif mode == 'chords':
    sound = 'chords'
    if (last_first_beat_for_record is None or
        last_first_beat == last_first_beat_for_record):
      curr_time = time.time()
      steps_per_second = int(qpm * 4 / 60)
      curr_time_step = sequences_lib.quantize_to_step(
          curr_time - last_first_beat, steps_per_second)
      playable_notes.add(PlayableNote(type='chords',
                               note=note,
                               instrument='chords',
                               onset=curr_time_step))
      last_first_beat_for_record = last_first_beat
  elif mode == 'improv':
    sound = 'wurly'
    # If we have data in our generated melody we substitute human's notes.
    if len(generated_melody):
      if improv_status != 'robot':
        improv_status = 'robot'
        print_status()
      # To avoid stuck notes, send a note off for previous mapped note.
      prev_note = list(args)
      prev_note[0] = note_mapping[args[0]]
      send_stopnote(prev_note)
      note_mapping[args[0]] = generated_melody[0]
      note[0] = generated_melody[0]
      note[1] *= improv_volume
      generated_melody = generated_melody[1:]
    else:
      if improv_status != 'psc':
        improv_status = 'psc'
        print_status()
      note[1] *= improv_volume
      accumulated_primer_melody.append(args[0])
    if len(accumulated_primer_melody) >= min_primer_length:
      magenta_thread = threading.Thread(target = generate_melody)
      magenta_thread.start()
  send_playnote(note, sound)


def process_note_off(addr, tags, args, source):
  """Handler for `/processnoteoff` messages from SuperCollider.

  If we're in improv_status == 'robot' and not improv mode, transpose
  notes an octave down, since that's what we did when sending the
  note to play.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global mode
  global note_mapping
  global last_first_beat_for_record
  global last_first_beat
  global playable_notes
  global qpm
  note = list(args)
  if mode == 'bass' or mode == 'chords':
    return
  orig_note = list(args)
  note = list(args)
  note[0] = note_mapping[args[0]]
  orig_note[0] = args[0]
  send_stopnote(note)
  # Just in case we also send a stopnote for original note.
  send_stopnote(orig_note)
  note_mapping[args[0]] = args[0]


def cc_event(addr, tags, args, source):
  """Handler for `/ccevent` messages from SuperCollider.

  Logic for dealine with the volume knob in the iRig mini
  keyboard.
  - If in lowest position (0): mode = 'tap'.
  - Else if in lower half of range, mode = 'bass'.
  - Else if in upper half (but not max), mode = 'chords'.
  - Else if at highest position (127): mode = 'improv'.

  Args:
    addr: Address message sent to.
    tags: Tags in message.
    args: Arguments passed in message.
    source: Source of sender.
  """
  global nanokontrol_id
  global mode
  global playable_instruments
  global time_signature
  global qpm
  global last_tap_onset
  global beat_length
  global last_first_beat_for_record
  global bass_line
  global playable_notes
  global seed_drum_sequence
  global temperature
  global bass_volume
  global num_bars
  global chords_volume
  global improv_volume
  global play_loop
  if not args:
    return
  cc_num, cc_chan, cc_src, cc_args = args
  if nanokontrol_id is None:
    nanokontrol_id = cc_args
    return
  if cc_args == nanokontrol_id:
    channel_name = nanokontrolmap.cc_messages[cc_chan][0]
    lowest_value = nanokontrolmap.cc_messages[cc_chan][2][0]
    highest_value = nanokontrolmap.cc_messages[cc_chan][2][1]
    # Logic for setting tempo, time signature, and looper.
    if channel_name == 'play' and cc_num == highest_value:
      play_loop = True
    elif channel_name == 'stop' and cc_num == highest_value:
      play_loop = False
    elif channel_name == 'track1_mute' and cc_num == highest_value:
      if 'click' in playable_instruments:
        playable_instruments.remove('click')
      else:
        playable_instruments.add('click')
    elif channel_name == 'track1_solo':
      if last_tap_onset is None:
        last_tap_onset = time.time()
        return
      curr_time = time.time()
      time_delta = curr_time - last_tap_onset
      last_tap_onset = curr_time
      if time_delta > MAX_TAP_DELAY:
        return
      if beat_length is None:
        beat_length = time_delta
      else:
        beat_length += time_delta
        beat_length /= 2
      beat_duration = time_signature.denominator / 2
      qpm = 60.0 / beat_length / beat_duration
    elif channel_name == 'track1_knob':
      qpm = 300 * cc_num / float(highest_value)
    elif channel_name == 'track_left' and cc_num == highest_value:
      time_signature.numerator = max(2, time_signature.numerator - 1)
      set_click()
    elif channel_name == 'track_right' and cc_num == highest_value:
      time_signature.numerator += 1
      set_click()
    elif channel_name == 'marker_left' and cc_num == highest_value:
      time_signature.denominator = max(4, time_signature.denominator / 2)
      set_click()
    elif channel_name == 'marker_right' and cc_num == highest_value:
      time_signature.denominator = min(16, time_signature.denominator * 2)
      set_click()
    elif channel_name == 'rew' and cc_num == highest_value:
      num_bars = max(1, num_bars - 1)
      set_click()
    elif channel_name == 'ff' and cc_num == highest_value:
      num_bars = min(4, num_bars + 1)
      set_click()
    # Logic for controlling the bass.
    elif channel_name == 'track2_slider':
      bass_volume = 5.0 * cc_num / float(highest_value)
      print_status()
    elif channel_name == 'track2_mute' and cc_num == highest_value:
      if 'bass' in playable_instruments:
        playable_instruments.remove('bass')
      else:
        playable_instruments.add('bass')
    elif channel_name == 'track2_record' and cc_num == highest_value:
      mode = 'bass'
      last_first_beat_for_record = None
      # Clear off last bass line.
      playable_notes = SortedList(
          [x for x in playable_notes if x.type != 'bass'],
          key=lambda x: x.onset)
      bass_line = []
    # Logic for controlling drums.
    elif channel_name == 'track3_solo' and cc_num == highest_value:
      mode = 'free'
      # Clear off last drum groove.
      playable_notes = SortedList(
          [x for x in playable_notes if x.type != 'drums'],
          key=lambda x: x.onset)
      seed_drum_sequence = music_pb2.NoteSequence()
      # First add a kick on each downbeat and hi-hats for each click.
      for playable_note in playable_notes:
        if playable_note.type != 'click':
          continue
        drum_note = seed_drum_sequence.notes.add()
        pitch = 42 if playable_note.instrument == 'click2' else 36
        drum_note.pitch = pitch
        drum_note.quantized_start_step = playable_note.onset
        drum_note.quantized_end_step = playable_note.onset + 4
        drum_note.is_drum = True
        playable_notes.add(PlayableNote(type='drums',
                                        note=[],
                                        instrument=DRUM_MAPPING[pitch],
                                        onset=playable_note.onset))
      # Now add snare hits that match the bass line.
      for bass_note in bass_line:
        drum_note = seed_drum_sequence.notes.add()
        pitch = 38
        drum_note.pitch = pitch
        drum_note.quantized_start_step = bass_note.onset
        drum_note.quantized_end_step = bass_note.onset + 4  # A quarter note.
        drum_note.is_drum = True
        playable_notes.add(PlayableNote(type='drums',
                                        note=[],
                                        instrument='snare',
                                        onset=bass_note.onset))
    elif channel_name == 'track3_mute' and cc_num == highest_value:
      if 'drums' in playable_instruments:
        playable_instruments.remove('drums')
      else:
        playable_instruments.add('drums')
    elif channel_name == 'track3_record' and cc_num == highest_value:
      mode = 'free'
      dt = threading.Thread(target = generate_drums)
      dt.start()
    elif channel_name == 'track3_knob':
      temperature = max(0.01, cc_num / float(highest_value) * 5.0)
    # Logic for controlling chords.
    elif channel_name == 'track4_slider':
      chords_volume = 5.0 * cc_num / float(highest_value)
      print_status()
    elif channel_name == 'track4_mute' and cc_num == highest_value:
      if 'chords' in playable_instruments:
        playable_instruments.remove('chords')
      else:
        playable_instruments.add('chords')
    elif channel_name == 'track4_record' and cc_num == highest_value:
      mode = 'chords'
      # Clear off last chords line.
      playable_notes = SortedList(
          [x for x in playable_notes if x.type != 'chords'],
          key=lambda x: x.onset)
      last_first_beat_for_record = None
    # Logic for controlling improv.
    elif channel_name == 'track5_slider':
      improv_volume = 5.0 * cc_num / float(highest_value)
      print_status()
    elif channel_name == 'track5_solo' and cc_num == highest_value:
      mode = 'free'
    elif channel_name == 'track5_record' and cc_num == highest_value:
      mode = 'improv'
  print_status()


def print_status():
  """Prints the status of the system."""
  global mode
  global improv_status
  global min_primer_length
  global max_robot_length
  global num_bars
  global accumulated_primer_melody
  global generated_melody
  global time_signature
  global temperature
  global qpm
  global bass_volume
  global chords_volume
  global improv_volume
  os.system('clear')
  print('mode: {}'.format(mode))
  print('num_bars: {}'.format(num_bars))
  print('{} / {} : {}'.format(time_signature.numerator,
                              time_signature.denominator,
                              qpm))
  print('temperature: {}'.format(temperature))
  print('bass_volume: {}'.format(bass_volume))
  print('chords_volume: {}'.format(chords_volume))
  print('improv_volume: {}'.format(improv_volume))
  if mode != 'improv':
    return
  print(ascii_arts.arts[improv_status])
  # if improv_status == 'psc':
  #   print('*' * len(accumulated_primer_melody) +
  #         '-' * (min_primer_length - len(accumulated_primer_melody)))
  # elif improv_status == 'robot':
  #   print('-' * (max_robot_length - len(generated_melody)) +
  #         '*' * (len(generated_melody)))


def main(_):
  tf.logging.set_verbosity(tf.logging.ERROR)
  os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
  set_click()
  print('please press any button on the nanokontrol2')
  
  # Set up and start the server.
  st = threading.Thread(target = server.serve_forever)
  st.start()
  server.addMsgHandler('/processnoteon', process_note_on)
  server.addMsgHandler('/processnoteoff', process_note_off)
  server.addMsgHandler('/ccevent', cc_event)
  # Start the looper.
  lt = threading.Thread(target = looper)
  lt.start()


if __name__ == '__main__':
  app.run(main)
