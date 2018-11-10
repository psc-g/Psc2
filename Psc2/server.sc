s.boot;
(

MIDIClient.init;

b = NetAddr.new("127.0.0.1", 12345);

// One slot per MIDI note, in global vars.
~thrunotes = Array.newClear(128);
~notes = Array.newClear(128);
~chordsnotes = Array.newClear(128);
~bassnotes = Array.newClear(128);

// Synth definitions.
SynthDef(\bass, { arg freq = 220, amp = 0.8, att = 0.01, rel = 0.5, lofreq = 1000, hifreq = 3000;
    var env, snd;
    env = Env.perc(
		attackTime: att,
		releaseTime: rel,
		level: amp
	).kr(doneAction: 2);
	snd = Saw.ar(freq: freq * [1.0, 1.0, 0.5, 0.5], mul: env);
    //snd = Saw.ar(freq: freq * [0.99, 1, 1.001, 1.008], mul: env);
	snd = LPF.ar(
		in: snd,
		freq: LFNoise2.kr(1).range(lofreq, hifreq)
	);
    snd = Splay.ar(snd);
    Out.ar(0, snd);
}).add;


SynthDef(\chords, { arg freq = 440, amp = 0.4, att = 0.1, rel = 2, lofreq = 1000, hifreq = 3000;
    var env, snd;
    env = Env.perc(
		attackTime: att,
		releaseTime: rel,
		level: amp
	).kr(doneAction: 2);
    snd = SinOsc.ar(freq: freq * [0.99, 1, 1.001, 1.008], mul: env);
	snd = LPF.ar(
		in: snd,
		freq: LFNoise2.kr(1).range(lofreq, hifreq)
	);
    snd = Splay.ar(snd);
    Out.ar(0, snd);
}).add;

SynthDef(\wurly, {
    |
    // standard meanings
    out = 0, freq = 440, gate = 1, pan = 0, amp = 0.1,
    // all of these range from 0 to 1
    vel = 0.8, modIndex = 0.2, mix = 0.2, lfoSpeed = 0.4, lfoDepth = 0.1
    |
    var env1, env2, env3, env4;
    var osc1, osc2, osc3, osc4, snd;

    lfoSpeed = lfoSpeed * 12;

    freq = freq * 2;

    env1 = EnvGen.ar(Env.adsr(0.001, 1.25, 0.0, 0.04, curve: \lin));
    env2 = EnvGen.ar(Env.adsr(0.001, 1.00, 0.0, 0.04, curve: \lin));
    env3 = EnvGen.ar(Env.adsr(0.001, 1.50, 0.0, 0.04, curve: \lin));
    env4 = EnvGen.ar(Env.adsr(0.001, 1.50, 0.0, 0.04, curve: \lin));

    osc4 = SinOsc.ar(freq * 0.5) * 2pi * 2 * 0.535887 * modIndex * env4 * vel;
    osc3 = SinOsc.ar(freq, osc4) * env3 * vel;
    osc2 = SinOsc.ar(freq * 15) * 2pi * 0.108819 * env2 * vel;
    osc1 = SinOsc.ar(freq, osc2) * env1 * vel;
    snd = Mix((osc3 * (1 - mix)) + (osc1 * mix));
    snd = snd * (SinOsc.ar(lfoSpeed) * lfoDepth + 1);

    // using the doneAction: 2 on the other envs can create clicks (bc of the linear curve maybe?)
    // snd = snd * EnvGen.ar(Env.asr(0, 1, 0.1), gate, doneAction: 2);
    snd = snd * EnvGen.ar(Env.asr(0, 1, 0.1), gate);
    snd = Pan2.ar(snd, pan, amp);

    Out.ar(out, snd);
}).add;

~thru = OSCFunc( { | msg, time, addr, port |
	m.noteOn(16, msg[1], msg[2]);
}, '/playthru' );

~stopthru = OSCFunc( { | msg, time, addr, port |
	m.noteOff(16, msg[1], msg[2]);
}, '/stopthru' );

~bass = OSCFunc( { | msg, time, addr, port |
	~bassnotes[msg[1]] = Synth(\bass, [\freq, msg[1].midicps, \amp, msg[2] * 0.00315]);
}, '/playbass' );

~stopbass = OSCFunc( { | msg, time, addr, port |
  if(~bassnotes[msg[1]].notNil) {
    ~bassnotes[msg[1]].free;
  };
}, '/stopbass' );

~chords = OSCFunc( { | msg, time, addr, port |
  if(~chordsnotes[msg[1]].notNil) {
    ~chordsnotes[msg[1]].free;
  };
	~chordsnotes[msg[1]] = Synth(\chords, [\freq, msg[1].midicps, \amp, msg[2] * 0.00315]);
}, '/playchords' );

~stopchords = OSCFunc( { | msg, time, addr, port |
  if(~chordsnotes[msg[1]].notNil) {
    ~chordsnotes[msg[1]].free;
  };
}, '/stopchords' );


~wurly = OSCFunc( { | msg, time, addr, port |
  if(~notes[msg[1]].notNil) {
    ~notes[msg[1]].free;
  };
	~notes[msg[1]] = Synth(\wurly, [\freq, msg[1].midicps, \amp, msg[2] * 0.00315]);
}, '/playwurly' );

~stopnote = OSCFunc( { | msg, time, addr, port |
  if(~notes[msg[1]].notNil) {
    ~notes[msg[1]].free;
  };
}, '/stopwurly' );

MIDIIn.connectAll;

~noteon = MIDIFunc.noteOn({ |veloc, num, chan, src|
	b.sendMsg("/processnoteon", num, veloc);
});

~noteoff = MIDIFunc.noteOff({ |veloc, num, chan, src|
	b.sendMsg("/processnoteoff", num, veloc);
});

~cc = MIDIFunc.cc({ |num, chan, src, args|
	b.sendMsg("/ccevent", num, chan, src, args);
});

~program = MIDIFunc.program({ |num, chan, src, args|
	b.sendMsg("/programevent", num, chan, src, args);
});

// Connect to the MIDI out controller.
m = MIDIOut(2);
m.latency = 0;
m.connect(2);
)
m.noteOff(16, 54, 60);
