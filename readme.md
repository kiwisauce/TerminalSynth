# TerminalSynth

TerminalSynth is a cross-platform Python application which synthesises audio. It is controlled with an interactive terminal interface.

## Pre-Requisites

Python >= 3.11

Python modules:
- pyaudio
- urwid

Windows:
```console
python -m pip install pyaudio
python -m pip install urwid
```

On Debian based Linux distibutions:
```console
apt install build-essential python3 portaudio19-dev python3-pyaudio python3-urwid
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
