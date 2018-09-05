# Bass doubler
This code allows you to control a "virtual" bass from a MIDI controller (i.e. a
keyboard). It consists of two main files:
*  *[`sc_server.scd`](./sc_server.scd):* SuperCollider server to transmit
   events from the external MIDI controller to/from the Python server.
*  *[`py_server.py`](./py_server.py):* Python server in charge of most of the
   logic.

I have only tested this on my setup (Linux), so no guarantees that it will work
anywhere else! Would be interested if it _does_ work for others in different
setups :).

## Install instructions
1.  Install [SuperCollider](https://supercollider.github.io/)

2.  Create a virtualenv and activate it. We need Python2 (and _not_ Python3)
    because `pyosc` is not compatible with Python3. This step is optional but
    recommended:

    ```
    virtualenv --system-site-packages -p python2 venv
    source venv/bin/activate
    ```

3.  `pip install pyosc`.

4.  Clone this repo.

5.  Open SuperCollider, open `sc_server.scd` and run each group (enclosed in
    parentheses) in order).

6.  Start the python server: 

    ```
    python py_server.py
    ```

7.  Make music!


## Hardware setup

My personal setup (and how I use this code) is: 

```
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
```

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
