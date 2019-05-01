# Psc2

Psc2 combines the worlds of jazz, rock, classical music, and artificial intelligence via original compositions and arrangements.

the compositions are built around the interplay of jazz harmonies, complex rhythms and extensive improvisation; many of them are composed in the "long-form" compositional style of classical music.

the arrangements take well-known songs from pop, rock and jazz and re-build them in a manner similar to our original compositions. the arrangements include songs by michael jackson, guns n' roses, silvio rodriguez, duke ellington and others.

psc is a señor swesearcher in google brain, and is experimenting with using machine learning models (including generative models for music) as part of the live performance. most of the code used will be available in this repo.

the white paper explaining the solo setting is available [here](https://arxiv.org/abs/1904.13285).

## Installation
1.  Install [SuperCollider](https://supercollider.github.io/)

1.  Clone this repo.

1.  Create a virtualenv and activate it. We need Python2 (and _not_ Python3)
    because `pyosc` is not compatible with Python3. This step is optional but
    recommended:

    ```
    virtualenv --system-site-packages -p python2 venv
    source venv/bin/activate
    cd Psc2
    pip install -r requirements.txt
    ```
    If the last command does not work, then:

    1.  `pip install absl-py`


    1.  `pip install pyosc`.

    1.  `pip install tensorflow`
        Full instructions [here](https://www.tensorflow.org/install/).

    1.  `pip install magenta`
         Full instructions [here](https://github.com/tensorflow/magenta).

1.  Download Melody RNN `attention_rnn` model
    [here](https://github.com/tensorflow/magenta/blob/2c3ae9b0dd64b06295e48e2ee5654e3d207035fc/magenta/models/melody_rnn/README.md),
    and update the `base_models_path` parameter in `Psc2/modes/mlsplainer.py`.

1.  Download DrumKit RNN model (for NeurIPS demo)
    [here](https://github.com/tensorflow/magenta/tree/2c3ae9b0dd64b06295e48e2ee5654e3d207035fc/magenta/models/drums_rnn).

1.  Open SuperCollider, open `Psc2/server.sc` and run the main group (enclosed
    in parentheses).

1.  From the root directory, run:

    ```
    python setup.py install
    ```

1.  Start the python server:

    ```
    python Psc2/server.py
    ```

