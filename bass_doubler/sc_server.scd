// Run the numbered groups in order.

// 1. Set up server and MIDIClient.
(
s.boot;

MIDIClient.init;

b = NetAddr.new("127.0.0.1", 12345);
)

// 2. Set up the callback to send an On event to the MIDI controller.
(
x = OSCFunc( { | msg, time, addr, port |
	m.noteOn(16, msg[1], msg[2]);
}, '/playnote' );
)

// 3. Set up the callback to send an Off event to the MIDI controller.
(
y = OSCFunc( { | msg, time, addr, port |
	m.noteOff(16, msg[1], msg[2]);
}, '/stopnote' );
)

// 4. Set up the callbacks from the MIDI controller, to send messages to Python.
(
var on, off, cc, bend;

MIDIIn.connectAll;


on = MIDIFunc.noteOn({ |veloc, num, chan, src|
	b.sendMsg("/processnoteon", num, veloc);
});

off = MIDIFunc.noteOff({ |veloc, num, chan, src|
	b.sendMsg("/processnoteoff", num, veloc);
});

cc = MIDIFunc.cc({ |num, chan, src, args|
	b.sendMsg("/ccevent", chan, num);
});


bend = MIDIFunc.bend({ |num, chan, src, args|
	b.sendMsg("/bendevent", num);
});

q = { on.free; off.free; };
)

// 5. Connect to the MIDI out controller.
(
m = MIDIOut(0);
m.latency = 0;
m.connect(1);
)

// *******************************
// Song-specific settings
// *******************************

// Solipair
(
  b.sendMsg("/sethighestbassnote", 54);
  b.sendMsg("/setoctaveshift", 1);
  b.sendMsg("/setbassnotedecay", 1.0);
)

// Espalda de Vidrio
(
  b.sendMsg("/sethighestbassnote", 54);
  b.sendMsg("/setoctaveshift", 1);
  b.sendMsg("/setbassnotedecay", 10.0);
)

// Mancuspias
(
  b.sendMsg("/sethighestbassnote", 57);
  b.sendMsg("/setoctaveshift", 0);
  b.sendMsg("/setbassnotedecay", 1.0);
)

// Run to turn off all notes if necessary.
m.allNotesOff(16);

// when done:
q.value;

