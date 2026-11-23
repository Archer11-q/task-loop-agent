from dataclasses import dataclass


@dataclass
class Todo:
    content:str
    is_done:bool=False