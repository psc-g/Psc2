s.boot;
(

MIDIClient.init;

b = NetAddr.new("127.0.0.1", 12345);

~notes = Array.newClear(128);  // One slot per MIDI note, in global var notes.
~chordsnotes = Array.newClear(128);  // One slot per MIDI note, in global var notes.
~bassnotes = Array.newClear(128);  // One slot per MIDI note, in global var notes.
~drums = Array.newClear(12);  // One slot per each drum hit.

// Set up the drum samples.
// I downloaded these samples from
// https://www.musicradar.com/news/drums/sampleradar-1000-free-drum-samples-229460
~samples_prefix = thisProcess.nowExecutingPath.dirname ++ "/audio/";
~kickb = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~kickb.free;
~kickb = Buffer.read(s, ~samples_prefix ++ "kick.wav");
~kick = SynthDef(\kick, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playkick = OSCFunc( { | msg, time, addr, port |
	~drums[0].free;
	~drums[0] = Synth(\kick, [\bufnum, ~kickb.bufnum]);
}, '/playkick' );
~stopkick = OSCFunc( { | msg, time, addr, port |
	~drums[0].free;
}, '/stopkick' );

~snareb = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~snareb.free;
~snareb = Buffer.read(s, ~samples_prefix ++ "snare.wav");
~snare = SynthDef(\snare, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playsnare = OSCFunc( { | msg, time, addr, port |
	~drums[1].free;
	~drums[1] = Synth(\snare, [\bufnum, ~snareb.bufnum]);
}, '/playsnare' );
~stopsnare = OSCFunc( { | msg, time, addr, port |
	~drums[1].free;
}, '/stopsnare' );

~ophatb = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~ophatb.free;
~ophatb = Buffer.read(s, ~samples_prefix ++ "ophat.wav");
~ophat = SynthDef(\ophat, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playophat = OSCFunc( { | msg, time, addr, port |
	~drums[2].free;
	~drums[2] = Synth(\ophat, [\bufnum, ~ophatb.bufnum]);
}, '/playophat' );
~stopophat = OSCFunc( { | msg, time, addr, port |
	~drums[2].free;
}, '/stopophat' );

~clhatb = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~clhatb.free;
~clhatb = Buffer.read(s, ~samples_prefix ++ "clhat.wav");
~clhat = SynthDef(\clhat, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playclhat = OSCFunc( { | msg, time, addr, port |
	~drums[3].free;
	~drums[3] = Synth(\clhat, [\bufnum, ~clhatb.bufnum]);
}, '/playclhat' );
~stopclhat = OSCFunc( { | msg, time, addr, port |
	~drums[3].free;
}, '/stopclhat' );

~tom1b = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~tom1b.free;
~tom1b = Buffer.read(s, ~samples_prefix ++ "tom1.wav");
~tom1 = SynthDef(\tom1, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playlowtom = OSCFunc( { | msg, time, addr, port |
	~drums[4].free;
	~drums[4] = Synth(\tom1, [\bufnum, ~tom1b.bufnum]);
}, '/playlowtom' );
~stoplowtom = OSCFunc( { | msg, time, addr, port |
	~drums[4].free;
}, '/stoplowtom' );

~tom2b = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~tom2b.free;
~tom2b = Buffer.read(s, ~samples_prefix ++ "tom2.wav");
~tom2 = SynthDef(\tom2, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playmidtom = OSCFunc( { | msg, time, addr, port |
	~drums[5].free;
	~drums[5] = Synth(\tom2, [\bufnum, ~tom2b.bufnum]);
}, '/playmidtom' );
~stopmidtom = OSCFunc( { | msg, time, addr, port |
	~drums[5].free;
}, '/stopmidtom' );

~tom3b = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~tom3b.free;
~tom3b = Buffer.read(s, ~samples_prefix ++ "tom3.wav");
~tom3 = SynthDef(\tom3, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playhightom = OSCFunc( { | msg, time, addr, port |
	~drums[6].free;
	~drums[6] = Synth(\tom3, [\bufnum, ~tom3b.bufnum]);
}, '/playhightom' );
~stophightom = OSCFunc( { | msg, time, addr, port |
	~drums[6].free;
}, '/stophightom' );

~crashb = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~crashb.free;
~crashb = Buffer.read(s, ~samples_prefix ++ "crash.wav");
~crash = SynthDef(\crash, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playcrash = OSCFunc( { | msg, time, addr, port |
	~drums[7].free;
	~drums[7] = Synth(\crash, [\bufnum, ~crashb.bufnum]);
}, '/playcrash' );
~stopcrash = OSCFunc( { | msg, time, addr, port |
	~drums[7].free;
}, '/stopcrash' );

~rideb = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~rideb.free;
~rideb = Buffer.read(s, ~samples_prefix ++ "ride.wav");
~ride = SynthDef(\ride, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playride = OSCFunc( { | msg, time, addr, port |
	~drums[8].free;
	~drums[8] = Synth(\ride, [\bufnum, ~rideb.bufnum]);
}, '/playride' );
~stopride = OSCFunc( { | msg, time, addr, port |
	~drums[8].free;
}, '/stopride' );

~click0b = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~click0b.free;
~click0b = Buffer.read(s, ~samples_prefix ++ "click0.wav");
~click0 = SynthDef(\click0, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playclick0 = OSCFunc( { | msg, time, addr, port |
	~drums[9].free;
	~drums[9] = Synth(\click0, [\bufnum, ~click0b.bufnum]);
}, '/playclick0' );
~stopclick0 = OSCFunc( { | msg, time, addr, port |
	~drums[9].free;
}, '/stopclick0' );

~click1b = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~click1b.free;
~click1b = Buffer.read(s, ~samples_prefix ++ "click1.wav");
~click1 = SynthDef(\click1, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playclick1 = OSCFunc( { | msg, time, addr, port |
	~drums[10].free;
	~drums[10] = Synth(\click1, [\bufnum, ~click1b.bufnum]);
}, '/playclick1' );
~stopclick1 = OSCFunc( { | msg, time, addr, port |
	~drums[10].free;
}, '/stopclick1' );

~click2b = Buffer.alloc(s, s.sampleRate * 2.0, 2);
~click2b.free;
~click2b = Buffer.read(s, ~samples_prefix ++ "click2.wav");
~click2 = SynthDef(\click2, { arg out = 0, bufnum;
	Out.ar( out, PlayBuf.ar(2, bufnum, BufRateScale.kr(bufnum))
	)
}).add;
~playclick2 = OSCFunc( { | msg, time, addr, port |
	~drums[11].free;
	~drums[11] = Synth(\click2, [\bufnum, ~click2b.bufnum]);
}, '/playclick2' );
~stopclick2 = OSCFunc( { | msg, time, addr, port |
	~drums[11].free;
}, '/stopclick2' );

// Synth definitions.
SynthDef(\bass, { arg freq = 220, amp = 0.8, att = 0.01, rel = 0.5, lofreq = 1000, hifreq = 3000;
    var env, snd;
    env = Env.perc(
		attackTime: att,
		releaseTime: rel,
		level: amp
	).kr(doneAction: 2);
	snd = Saw.ar(freq: freq * [0.25, 0.25, 0.5, 0.5], mul: env);
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
}, '/stopnote' );

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

q = { ~noteon.free; ~noteoff.free; };
)
