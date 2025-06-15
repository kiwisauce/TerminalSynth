# TerminalSynth

TerminalSynth is a cross-platform Python application which synthesises audio. It is controlled with an interactive terminal interface.

## Pre-Requisites

Python >= 3.11

Python modules:
- pyaudio
- urwid

Windows:
```console
python -m pip install sounddevice
python -m pip install urwid
python -m pip install numpy
```

On Debian based Linux distibutions:
```console
apt install build-essential python3 portaudio19-dev python3-venv
python3 -m venv ./.venv
source .venv/bin/activate
pip install sounddevice urwid numpy
```

## Usage

On Windows:
```console
python app.py
```

On Linux:
```console
./app.py
```

## License

[MIT](https://choosealicense.com/licenses/mit/)
