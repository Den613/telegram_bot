import logging

from aiogram import Bot, Router
from aiogram.filters import LEAVE_TRANSITION, ChatMemberUpdatedFilter, CommandStart
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    Message,
)

from aiogram.utils.markdown import hbold, hcode
from devtools import debug
from time_select import InputDate
from update_message import update_messages
from models import Operation
from global_dict import user_states, user_current_text_kbd
from calendar import monthrange
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = Router()


@router.message(CommandStart())
async def command_start_handler(message: Message, bot: Bot) -> None:
    logger.warning(f'{message.message_id}')

    month = 2
    _, to_d = monthrange(2023, month)
    user_states[message.from_user.id] = InputDate(
    
        start_from=datetime(year=2023, month=month, day=1, hour=0, minute=0),
        stop_from=datetime(year=2023, month=month, day=to_d),       
        minute_step=10
    )

    await update_messages(bot, message=message)
   

@router.chat_member()
async def chat_member_update(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        f"Member {hcode(chat_member.from_user.id)} was changed "
        + f"from {chat_member.old_chat_member.status} to {chat_member.new_chat_member.status}",
    )


# this router will use only callback_query updates
sub_router = Router()

@sub_router.callback_query()
async def callback_tap_me(callback_query: CallbackQuery, bot: Bot) -> None:    
    user_id = callback_query.from_user.id
    op = None
    r = await user_states[user_id].callback(callback_query)    
    
    if r is not None:
        op = Operation.NEXT
    
    op = await update_messages(bot, op, user_id=user_id, value=r)
    if op == Operation.STOP:
        # send result somewhere
        await callback_query.answer(f"Yeah good, now I'm fine {r}")
        print(f'result for user{user_id}: {r}')
        del user_states[user_id]
        del user_current_text_kbd[user_id]


# this router will use only edited_message updates
sub_sub_router = Router()

@sub_sub_router.edited_message()
async def edited_message_handler(edited_message: Message) -> None:
    await edited_message.reply("Message was edited, Big Brother watches you")


# this router will use only my_chat_member updates
deep_dark_router = Router()

@deep_dark_router.my_chat_member(~ChatMemberUpdatedFilter(~LEAVE_TRANSITION))
async def my_chat_member_change(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    await bot.send_message(
        chat_member.chat.id,
        f"This Bot`s status was changed from {hbold(chat_member.old_chat_member.status)} "
        f"to {hbold(chat_member.new_chat_member.status)}",
    )
