# Bass doubler
This code allows you to control a "virtual" bass from a MIDI controller (i.e. a
keyboard).

My personal setup (and how I use this code) is: 

Roland keyboard ------ regular 1/4" -----> keyboard amplifier
              |
            MIDI
              |
              v
         Computer ( SuperCollider <-----> Python )
              |
            MIDI
              |
              v
      Roland GAIA ---- regular 1/4" -----> bass amplifier

I'm using a bass sound on the Roland GAIA.

The SuperCollider code is just a tunnel for MIDI, as I don't know how to use it
very well.  It receives MIDI note on/off messages from the Roland XC-3000, as
well as control (sustain pedal) and bend events, and redirects everything to
the Python server.

The Python server does all the fancy logic for figuring when to play the bass
note and for how long. It will send note on/off messages back to SuperCollider,
which will then transmit this to the Roland GAIA for bass playback.

*   You can turn the Python server on/off by moving the bend stick to the right.
*   You can change the highest bass note by holding the bend stick to the left
    and hitting a key on the Roland XC3000.
*   There's some non-trivial logic for dealing with the interaction between
    bass notes and the sustain pedal. This is specific to my style of playing,
    but I imagine other people have similar techniques.
