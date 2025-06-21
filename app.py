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
prev_sine_progress = 0.0
kick_mode_active = False
kick_frequency_hz = 10000.0

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
        "K": 12, # C
    }

    if key.upper() not in note_index_from_keyboard_keys:
        return -1 # Something else can handle this key.

    note_index = note_index_from_keyboard_keys[key.upper()]
    note_index_root_c = octave * 12 - 8
    return note_index_root_c + note_index

def generate_sine_waveform(samples_per_period,**kwargs):
    def sine(x):
        if kick_mode_active:
            return np.clip(4 * np.sin(x),-1.0,1.0)
        else:
            return np.sin(x)

    start = kwargs["start"] if "start" in kwargs else 0
    end = np.pi * 2

    nr_samples = int(samples_per_period * (1 - start / (2 * np.pi)))
    if nr_samples < 1:
        return np.array([])

    sample_indexes = np.linspace(start,end,nr_samples)
    return np.apply_along_axis(sine,axis=0,arr=sample_indexes)

def piano_roll_callback(outdata,frames,time,status):
    global kick_mode_active
    global kick_frequency_hz
    global frequency_hz
    global prev_sine_progress

    if kick_frequency_hz < frequency_hz:
        kick_frequency_hz = 10000.0

    if kick_mode_active:
        samples_per_period = int(44100 / kick_frequency_hz)
    else:
        samples_per_period = int(44100 / frequency_hz)

    # Generate the remainder of the waveform that was abandoned when we ran out of frames in the previous callback.
    remainder_sine_waveform = generate_sine_waveform(samples_per_period,start = prev_sine_progress * np.pi * 2)
    full_sine_waveform = generate_sine_waveform(samples_per_period)

    remaining_samples_in_callback = frames

    # Start with the remainder.
    waveform = remainder_sine_waveform
    remaining_samples_in_callback -= len(waveform)

    while remaining_samples_in_callback > samples_per_period:
        if kick_mode_active:
            samples_per_period = int(44100 / kick_frequency_hz)
            full_sine_waveform = generate_sine_waveform(samples_per_period=samples_per_period)
            kick_frequency_hz *= 0.92

        waveform = np.concatenate([waveform,full_sine_waveform])
        remaining_samples_in_callback -= samples_per_period

    waveform = np.concatenate([waveform,full_sine_waveform[0:remaining_samples_in_callback]])
    # We must abandon the waveform as we have run out of frames. Store our progress for the 
    # next callback so we can generate the remainder of the waveform in the next callback.
    prev_sine_progress = remaining_samples_in_callback / samples_per_period

    outdata[:] = waveform[:frames].reshape(frames,1)

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
        piano_key_nr -= 12
    if key.upper() == "X" and octave < 6:
        octave += 1
        piano_key_nr += 12

    if keyboard_key_to_piano_key_nr(key) != -1:
        piano_key_nr = keyboard_key_to_piano_key_nr(key)

    frequency_hz = 440.0 * pow(1.059463,piano_key_nr - 49)

    note_text = urwid.Text(f"Note: {piano_key_nr_to_string(piano_key_nr)}",align="center")
    octave_down_text = urwid.Text("Z: Octave down",align="left")
    octave_up_text = urwid.Text("X: Octave up",align="left")
    exit_text = urwid.Text("Q: Stop audio",align="left")
    pile = urwid.Pile([note_text,octave_down_text,octave_up_text,exit_text])
    loop.widget = urwid.Filler(pile)

def kick_mode_activate(loop):
    global kick_mode_active

    kick_mode_active = True

def kick_mode_deactivate(loop):
    global kick_mode_active

    kick_mode_active = False

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
        },
        {
            "activation_key": "9",
            "description": "Activate Kick Mode",
            "action": kick_mode_activate,
        },
        {
            "activation_key": "8",
            "description": "Dectivate Kick Mode",
            "action": kick_mode_deactivate,
        },
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