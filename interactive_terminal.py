from abc import abstractmethod,ABC
from typing import Self
import inspect

class MenuItem(ABC):
    def __init__(self,config: dict,parent: Self) -> None:
        self._activation_key = config["activation_key"]
        self.description = config["description"]
        self._parent = parent
        self.active = False

    def press_key(self,key: str) -> bool:
        if self._parent is not None:
            if key == self._activation_key and self._parent.active is True:
                self.activate()
        if key == "q" and self.active:
            self._deactivate()
            if self._parent is None:
                return True # Exit.
        return False # Continue.
	
    def print_info(self) -> None:
        print(f"{self._activation_key}: {self.description}")

    @abstractmethod
    def activate(self) -> None:
        pass

    def _deactivate(self) -> None:
        self.active = False
        if self._parent is not None:
            self._parent.activate()

class Menu(MenuItem):
    def __init__(self,config,parent) -> None:
        super().__init__(config,parent)
        self._children = list()
        for child_config in config["children"]:
            child = menu_item_new(child_config,self)
            self._children.append(child)
    
    def press_key(self,key) -> bool:
        finished = super().press_key(key)
        
        for child in self._children:
            child.press_key(key)

        return finished

    def activate(self) -> None:
        super().activate()
        print(f"Current Menu: {self.description}")
        print("Options:")
        for child in self._children:
            child.print_info()

        if self._parent is not None:
            self._parent.active = False
            print(f"q: Go to {self._parent.description}")
        else:
            print("q: Exit Program")
        self.active = True
        print()

class Action(MenuItem):
    def __init__(self,config,parent):
        super().__init__(config,parent)
        self._action = config["action"]
        if not inspect.isfunction(self._action):
            ValueError('"action" must be a function')
        
    def activate(self):
        self._action()

class KeyHandler(MenuItem):
    def __init__(self,config,parent):
        super().__init__(config,parent)
        self._key_handler = config["handler"]

    def activate(self) -> None:
        self._parent.active = False
        self.active = True

    def press_key(self,key):
        super().press_key(key)
        if self.active:
            if self._key_handler(key): # This returns True if it has finished.
                self._deactivate()
        return False

def menu_item_new(config,parent):
    if "children" in config:
        assert "action" not in config and "handler" not in config
        return Menu(config,parent)
    elif "action" in config:
        assert "children" not in config and "handler" not in config
        return Action(config,parent)
    elif "handler" in config:
        assert "children" not in config and "action" not in config
        return KeyHandler(config,parent)
    else:
        assert False
