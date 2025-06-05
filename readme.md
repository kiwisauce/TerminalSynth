# TerminalSynth

TerminalSynth is a cross-platform Python application which synthesises audio. It is controlled with an interactive terminal interface.

## Pre-Requisites

Python >= 3.11

Python modules:
- pyaudio
- urwid

Please install the python modules as so:
On Windows:
Ensure python is installed and added to PATH and then run:
```console
python -m pip install pyaudio
python -m pip install urwid
```

On Debian based Linux distibutions:
```console
apt install build-essential
apt install python3
apt install portaudio19-dev
apt install python3-pyaudio
apt install python3-urwid
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
