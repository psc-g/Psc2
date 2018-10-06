s.freeAll;  // Safety latch is organ sound gets stuck.
(  // Run this main loop to get everything going, may take a few seconds.

var on, off, cc, bend;

~step1 = {

s.boot;

MIDIClient.init;

b = NetAddr.new("127.0.0.1", 12345);

~notes = Array.newClear(128);  // One slot per MIDI note, in global var notes.

// TODO(psc): Figure out why the notes with this instrument sometimes get stuck.
SynthDef(\organ, { |out, freq=440, amp=0.1, gate=1|
    var snd;
    snd = Splay.ar(SinOsc.ar(freq*Array.geom(4,1,2), mul:1/4));
    snd = snd + SinOsc.ar(freq/2, mul:0.4)!2;
    snd = snd * EnvGen.ar(Env.asr(0.001,1,0.01), gate, doneAction:2);
    OffsetOut.ar(out, snd * amp);
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
    snd = snd * EnvGen.ar(Env.asr(0, 1, 0.1), gate, doneAction: 2);
    snd = Pan2.ar(snd, pan, amp);

    Out.ar(out, snd);
}).add;
};
~step1.value;

x = OSCFunc( { | msg, time, addr, port |
	~notes[msg[1]] = Synth(\organ, [\freq, msg[1].midicps, \amp, msg[2] * 0.00315]);
}, '/playorgan' );


w = OSCFunc( { | msg, time, addr, port |
	~notes[msg[1]] = Synth(\wurly, [\freq, msg[1].midicps, \amp, msg[2] * 0.00315]);
}, '/playwurly' );


y = OSCFunc( { | msg, time, addr, port |
	~notes[msg[1]].release;
}, '/stopnote' );

~step2 = {
MIDIIn.connectAll;


on = MIDIFunc.noteOn({ |veloc, num, chan, src|
	b.sendMsg("/processnoteon", num, veloc);
});

off = MIDIFunc.noteOff({ |veloc, num, chan, src|
	b.sendMsg("/processnoteoff", num, veloc);
});

cc = MIDIFunc.cc({ |num, chan, src, args|
	b.sendMsg("/ccevent", num, chan, src, args);
});

q = { on.free; off.free; };
};
~step2.value;

~drumkit = {
// Basic drum kit

SynthDef("hihat", {arg out = 0, amp = 0.5, att = 0.01, rel = 0.2, ffreq = 6000, pan = 0;
	var env, snd;
	env = Env.perc(att, rel, amp).kr(doneAction: 2);
	snd = WhiteNoise.ar;
	snd = HPF.ar(in: snd, freq: ffreq, mul: env);
	Out.ar(out, Pan2.ar(snd, pan));
}).add;

SynthDef("snare", {arg out = 0, amp = 0.1, sinfreq = 180, att = 0.01, rel = 0.2, ffreq = 2000, pan = 0;
	var env, snd1, snd2, sum;
	env = Env.perc(att, rel, amp).kr(doneAction: 2);
	snd1 = HPF.ar(
		in: WhiteNoise.ar,
		freq: ffreq,
		mul: env
	);
	snd2 = SinOsc.ar(freq: sinfreq, mul: env);
	sum = snd1 + snd2;
	Out.ar(out, Pan2.ar(sum, pan));
}).add;

SynthDef("kick", {arg out = 0, amp = 0.3, sinfreq = 60, glissf = 0.9, att = 0.01, rel = 0.45, pan = 0;
	var env, snd, ramp;
	env = Env.perc(att, rel, amp).kr(doneAction: 2);
	ramp = XLine.kr(
		start: sinfreq,
		end: sinfreq * glissf,
		dur: rel
	);
	snd = SinOsc.ar(freq: ramp, mul: env);
	snd = Pan2.ar(snd, pan);
	Out.ar(out, snd);
}).add;

// Basic saw synth for chords and bass
SynthDef("sawSynth", { arg freq = 440, amp = 0.1, att = 0.1, rel = 2, lofreq = 1000, hifreq = 3000;
    var env, snd;
    env = Env.perc(
		attackTime: att,
		releaseTime: rel,
		level: amp
	).kr(doneAction: 2);
    snd = Saw.ar(freq: freq * [0.99, 1, 1.001, 1.008], mul: env);
	snd = LPF.ar(
		in: snd,
		freq: LFNoise2.kr(1).range(lofreq, hifreq)
	);
    snd = Splay.ar(snd);
    Out.ar(0, snd);
}).add;
};
~drumkit.value;

~groove = {
Pbind(
	\instrument, "hihat",
	\dur, Pseq([1/16, Rest(1/16)], inf),
	\att, 0.01,
	\rel, 0.1,
	\ffreq, 11000,
	\pan, 0,
	\amp, 0.3
).play;

Pbind(
	\instrument, "snare",
	\dur, Pseq([Rest(1/2), 1/2], inf),
	\att, 0.01,
	\rel, 0.1,
	\sinfreq, 180,
	\ffreq, 2000,
	\amp, 0.25

).play;

Pbind(
	\instrument, "kick",
	\dur, Pseq([3/4, 1/8, 1/8, 1, 1/4, 1/2, 1/4, 1/2, 1/2], inf),
	\att, 0.01,
	\rel, 0.22,
	\sinfreq, 60,
	\glissf, 0.9,
	\amp, 1,
).play;

// Chords
Pbind(
	\instrument, "sawSynth",
    \midinote, Pseq([
		Prand([[45, 48, 50, 53], [45, 48, 50]]),
		Prand([[43, 48, 50, 43], [43, 48, 50]]),
		Prand([[43, 48, 50, 52], [43, 48, 50]]),
		Prand([[41, 45, 46, 50], [41, 45, 46]]),
		Prand([[40, 45, 49, 52], [40, 45, 49]])
		], inf),
    \dur, Pseq([1, 1, 1, 1/2, 1/2], inf),
	\att, 0.1,
	\rel, Pkey(\dur) + 1,
	\hifreq, 5000,
    \amp, 0.2
).play;

// Bassline
Pbind(
	\instrument, "sawSynth",
	\midinote, Pseq([50, 48, 45, 43, 48, 48, 41, 46, 45], inf),
	\dur, Pseq([3/4, 1/8, 1/8, 1, 1/4, 1/2, 1/4, 1/2, 1/2], inf),
	\ctranspose, [0, -12],
	\att, 0.01,
	\rel, 0.2,
	\amp, 0.4,
	\lofreq, 100,
	\hifreq, 1000
).play;
};
~groove.value;

)
