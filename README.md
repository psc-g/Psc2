# Psc2

psc is a señor swesearcher in google brain, and is experimenting with using machine learning models (including generative models for music) as part of the live performance. most of the code used will be available in this repo.

if you want to see the code i use for my talks, you can see it [here](https://github.com/psc-g/Psc2/tree/master/talks/arturia).

*NEW:* i built a web app to make it easier for you to try out this idea! check it out [here](https://ml-jam.glitch.me/).

the white paper explaining the solo setting is available [here](https://arxiv.org/abs/1904.13285).

if you want the full-blown system, continue reading.

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

