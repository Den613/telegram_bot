from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any
from aiogram.types import InlineKeyboardButton


class Operation(Enum):
    START = auto()
    NEXT = auto()
    STOP = auto()

@dataclass
class KbdContent:
    kbd: list[list[InlineKeyboardButton]]
    text: str = field(default='')

@dataclass
class Content(KbdContent):
    pass

@dataclass
class DialogState(KbdContent):
    message_id: int = field(default=0)
    chat_id: int = field(default=0)
    obj: Any = field(default=None)