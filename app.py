#!/usr/bin/env python3

import asyncio
import interactive_terminal
import numpy as np
import selectors
import sounddevice as sd
import urwid

# Globals
octave = 4
piano_key_nr = 49
frequency_hz = 440.0
prev_sample = -0.5

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

def piano_roll_callback(outdata,frames,time,status):
    global frequency_hz
    global prev_sample

    samples_per_period = int(44100 / frequency_hz)

    samples_left = samples_per_period - (samples_per_period * ((prev_sample + 0.5) / 1.0))

    single_sawtooth_waveform = np.linspace(-0.5,0.5,samples_per_period).reshape(samples_per_period,1)

    samples_left = min(int(samples_per_period - (samples_per_period * ((prev_sample + 0.5) / 1.0))),frames)
    partial_waveform = np.linspace(prev_sample,0.5,samples_left).reshape(samples_left,1)
    remaining_waveform = np.resize(single_sawtooth_waveform,frames - samples_left).reshape(frames - samples_left,1)
    waveform = np.concatenate([partial_waveform,remaining_waveform])

    outdata[:] = waveform[:frames].reshape(frames,1)
    prev_sample = outdata[-1].item()

async def task_finished():
    while stream_continue == True:
        await asyncio.sleep(0)

async def piano_roll_task():
    with sd.OutputStream(callback=piano_roll_callback,samplerate=44100,channels=1):
        await task_finished()

def piano_roll_activate(loop):
    global stream_continue
    global prev_sample

    prev_sample = -0.5

    stream_continue = True

    asyncio.create_task(piano_roll_task())

def piano_roll_deactivate(loop):
    global stream_continue

    stream_continue = False

def piano_roll_key_handler(loop,key):
    global frequency_hz
    global piano_key_nr
    global octave

    if key.upper() == "Z" and octave > 1:
        octave -= 1
    if key.upper() == "X" and octave < 6:
        octave += 1
    if keyboard_key_to_piano_key_nr(key) != -1:
        piano_key_nr = keyboard_key_to_piano_key_nr(key)

    frequency_hz = 440.0 * pow(1.059463,piano_key_nr - 49)

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