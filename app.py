from pynput import keyboard
import interactive_terminal
import asyncio

def print_b():
    print("B\n")

def print_d1():
    print("D1\n")

def print_d2():
    print("D2\n")

def handler(key: str) -> bool:
    print(key)
    if key == "p":
        return True # Exit.
    return False # Continue

root_config = {
    "description": "Main Menu",
    "activation_key": "l",
    "children": [
        {
            "activation_key": "d",
            "description": "Print D1",
            "action": print_d1
        },
        {
            "activation_key": "e",
            "description": "Echo",
            "handler": handler
        },
        {
            "activation_key": "a",
            "description": "Menu A",
            "children": [
                {
                    "activation_key": "b",
                    "description": "Print B",
                    "action": print_b
                },
                {
                    "activation_key": "c",
                    "description": "Menu C",
                    "children": [
                        {
                            "activation_key": "d",
                            "description": "Print D2",
                            "action": print_d2
                        }
                    ]
                }
            ]
        },
    ]
}

def transmit_keys():
    queue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    def on_release(key):
        if hasattr(key,"char"):
            loop.call_soon_threadsafe(queue.put_nowait,key.char)
    keyboard.Listener(on_release=on_release).start()
    return queue

async def main():
    root_menu = interactive_terminal.menu_item_new(root_config,None)
    root_menu.activate()
    key_queue = transmit_keys()
    finished = False
    while not finished:
        key = await key_queue.get()
        finished = root_menu.press_key(key)

asyncio.run(main())
exit()