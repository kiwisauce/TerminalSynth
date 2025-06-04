from abc import abstractmethod,ABC
from typing import Self
import inspect
import urwid

class MenuItem(ABC):
    def __init__(self,config: dict,parent: Self,loop) -> None:
        self._activation_key = config["activation_key"]
        self.description = config["description"]
        self._parent = parent
        self._loop = loop
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
	
    def get_info(self) -> str:
        return f"{self._activation_key}: {self.description}"

    @abstractmethod
    def activate(self) -> None:
        pass

    def _deactivate(self) -> None:
        self.active = False
        if self._parent is not None:
            self._parent.activate()

class Menu(MenuItem):
    def __init__(self,config,parent,loop) -> None:
        super().__init__(config,parent,loop)
        self._children = list()
        for child_config in config["children"]:
            child = menu_item_new(child_config,self,self._loop)
            self._children.append(child)
    
    def press_key(self,key) -> bool:
        finished = super().press_key(key)
        
        for child in self._children:
            child.press_key(key)

        return finished

    def activate(self) -> None:
        super().activate()
        title = urwid.Text(self.description,align="center")
        div = urwid.Divider()
        pile = urwid.Pile([title,div])
        for child in self._children:
            option = urwid.Text(child.get_info())
            pile.contents.append((option,pile.options()))

        if self._parent is not None:
            self._parent.active = False
            exit_str = f"q: Go to {self._parent.description}"
        else:
            exit_str = "q: Exit Program"
        exit_text = urwid.Text(exit_str)
        pile.contents.append((exit_text,pile.options()))

        self._loop.widget = urwid.Filler(pile)
        self.active = True

class Action(MenuItem):
    def __init__(self,config,parent,loop):
        super().__init__(config,parent,loop)
        self._action = config["action"]
        if not inspect.isfunction(self._action):
            ValueError('"action" must be a function')
        
    def activate(self):
        self._action(self._loop)

def menu_item_new(config,parent,loop):
    if "children" in config:
        assert "action" not in config and "handler" not in config
        return Menu(config,parent,loop)
    elif "action" in config:
        assert "children" not in config and "handler" not in config
        return Action(config,parent,loop)
    else:
        assert False
