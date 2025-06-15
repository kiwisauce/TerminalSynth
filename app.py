#!/usr/bin/env python3

import asyncio
import interactive_terminal
import pyaudio
import selectors
import urwid

# Globals

def piano_key_nr_to_string(piano_key_nr: int) -> str:
    note_strings = {
        0:  "C",
        1:  "C#",
        2:  "D",
        3:  "D#",
        4:  "E",
        5:  "F",
        6:  "F#",
        7:  "G",
        8:  "G'",
        9:  "A",
        10: "A#",
        11: "B",
    }
    octave = int((piano_key_nr + 8) / 12)
    note_index = (piano_key_nr + 8) % 12
    return f"{note_strings[note_index]}{octave}"

def keyboard_key_to_piano_key_nr(key: str) -> int:
    global octave

    note_index_from_keyboard_keys = {
        "A": 0,  # C
        "W": 1,  # C#
        "S": 2,  # D
        "E": 3,  # D#
        "D": 4,  # E
        "F": 5,  # F
        "T": 6,  # F#
        "G": 7,  # G
        "Y": 8,  # G#
        "H": 9,  # A
        "U": 10, # A#
        "J": 11, # B
    }

    if key.upper() not in note_index_from_keyboard_keys:
        return -1 # Something else can handle this key.

    note_index = note_index_from_keyboard_keys[key.upper()]
    note_index_root_c = octave * 12 - 8
    return note_index_root_c + note_index

def piano_roll_callback(in_data,frame_count,time_info,status):
    global piano_key_nr
    global sample

    data = list()

    _sample = sample
    for frame_index in range(frame_count * 2):
        data.append(int(_sample))
        next_sample = _sample + slope
        _sample = next_sample if next_sample <= 255.0 else 0.0

    sample = _sample
    return (bytes(data),pyaudio.paContinue)

def piano_roll_activate(loop):
    global pa
    global stream
    global sample

    sample = 0.0

    stream = pa.open(format=pa.get_format_from_width(1,True),
                    channels=1,
                    rate=44100,
                    output=True,
                    frames_per_buffer=4096,
                    stream_callback=piano_roll_callback)

def piano_roll_deactivate(loop):
    global stream

    stream.stop_stream()
    stream.close()

def piano_roll_key_handler(loop,key):
    global slope
    global piano_key_nr
    global octave
    
    if keyboard_key_to_piano_key_nr(key) != -1:
        piano_key_nr = keyboard_key_to_piano_key_nr(key)
        frequency_hz = 440.0 * pow(1.059463,piano_key_nr - 49)
        slope = 255.0 * frequency_hz / 44100.0

    if key.upper() == "Z" and octave > 1:
        octave -= 1
    if key.upper() == "X" and octave < 6:
        octave += 1

    note_text = urwid.Text(piano_key_nr_to_string(piano_key_nr),align="center")
    loop.widget = urwid.Filler(note_text)

root_config_new = {
    "description": "Main Menu",
    "activation_key": "l",
    "children": [
        {
            "activation_key": "0",
            "description": "Play Piano Roll",
            "key_handler": piano_roll_key_handler,
            "activate": piano_roll_activate,
            "deactivate": piano_roll_deactivate
        }
    ]
}

def key_handler(key):
    global menu

    if len(key) > 1:
        return # Ignore mouse clicks

    if menu.press_key(key) == True:
        raise urwid.ExitMainLoop()

if __name__ == "__main__":
    placeholder = urwid.SolidFill()
    selector = selectors.SelectSelector()
    async_loop = asyncio.SelectorEventLoop(selector)
    urwid_async_loop = urwid.AsyncioEventLoop(loop=async_loop)
    loop = urwid.MainLoop(placeholder,unhandled_input=key_handler,event_loop=urwid_async_loop)

    menu = interactive_terminal.menu_item_new(root_config_new,None,loop)
    menu.activate()

    loop.run()