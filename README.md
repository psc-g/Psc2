# Psc2

Psc2 combines the worlds of jazz, rock, classical music, and artificial intelligence via original compositions and arrangements.

the compositions are built around the interplay of jazz harmonies, complex rhythms and extensive improvisation; many of them are composed in the "long-form" compositional style of classical music.

the arrangements take well-known songs from pop, rock and jazz and re-build them in a manner similar to our original compositions. the arrangements include songs by michael jackson, guns n' roses, silvio rodriguez, duke ellington and others.

psc is a señor swesearcher in google brain, and is experimenting with using machine learning models (including generative models for music) as part of the live performance. most of the code used will be available in this repo.

## Installation
1.  Install [SuperCollider](https://supercollider.github.io/)

2.  Create a virtualenv and activate it. We need Python2 (and _not_ Python3)
    because `pyosc` is not compatible with Python3. This step is optional but
    recommended:

    ```
    virtualenv --system-site-packages -p python2 venv
    source venv/bin/activate
    ```

3.  `pip install pyosc`.

4.  Install Tensorflow (instructions
    [here](https://www.tensorflow.org/install/)).

5.  Install Magenta (instructions [here](https://github.com/tensorflow/magenta)).

4.  Clone this repo.

5.  Open SuperCollider, open `Psc2/server.sc` and run the main group (enclosed
    in parentheses).

6.  From the root directory, run:

    ```
    python setup.py install
    ```

7.  Start the python server:

    ```
    python Psc2/server.py
    ```

