from aiogram.types import (    
    InlineKeyboardMarkup,
    Message
)
import logging

from typing import Any
from devtools import debug
from dataclasses import asdict

from models import DialogState, Operation
from aiogram import Bot

from global_dict import user_states, user_current_text_kbd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def update_messages(bot: Bot, op: Operation = Operation.START, user_id: int|None = None, message: Message|None = None, value: Any = None):

    text_ = ''
    
    if user_id is None and not message:
        raise ValueError(f'user_id or message should be specified and valid {user_id}, {message}')    
    if user_id is None:
        user_id = message.from_user.id # (from message)        
                    
    obj = user_states[user_id]     

    # if user_id is None and not obj:
    #     raise ValueError('user_id and object specified and valid')
    
    state = user_current_text_kbd.get(user_id)    
    content = await obj.content(op=op)

    if not content.kbd:
        op = Operation.STOP

    text = text_ + content.text
        
    match(op):
        case Operation.START:
            
            state = user_current_text_kbd[user_id] = DialogState(**asdict(content), obj=obj)        
            r = await message.answer(
                text+'Date',
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=content.kbd
                    
                ),
            )
            
            logger.warning(f'{r.message_id}')
            state.message_id = r.message_id        
            state.chat_id = r.chat.id
                    
        case Operation.NEXT:
        
            if state.kbd != content.kbd and state.text == content.text:
                await bot.edit_message_reply_markup(
                    state.chat_id,
                    state.message_id,
                        reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=content.kbd
                        ),
                )
                
                state.kbd = content.kbd
            if state.text != text:
                
                await bot.edit_message_text(
                    text,
                    state.chat_id,
                    state.message_id,
                    reply_markup=InlineKeyboardMarkup(
                            inline_keyboard=content.kbd
                    ),
                )
                state.text = content.text
                                        
        case Operation.STOP:
            await bot.edit_message_text(
                text,
                state.chat_id,
                state.message_id,
            )
        case _:
            raise ValueError('Unknown operation')

    return op