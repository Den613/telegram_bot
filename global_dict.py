from typing import Any
from models import DialogState

user_states: dict[int, Any] = {}

user_current_text_kbd: dict[int, DialogState] = {}