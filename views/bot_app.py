import random
import string

from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.auth import Account
from models.settings import settings

ADMIN_TG = set([int(x) for x in settings.ADMIN_TG.split()])

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()


class UserState(StatesGroup):
    type_username = State()
    status_user = State()


@dp.message(CommandStart(), F.chat.id.in_(ADMIN_TG))
async def command_start_handler(message: Message) -> None:
    kb = [
        [KeyboardButton(text="/create_user", )],
        [KeyboardButton(text="/change_status_user")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb)
    await message.answer(f"Hello, {message.from_user.id}!", reply_markup=keyboard)


@dp.message(Command('create_user'), F.chat.id.in_(ADMIN_TG))
async def create_user(message: Message, state: FSMContext) -> None:
    await message.answer(text="Type username")
    await state.set_state(UserState.type_username)


@dp.message(UserState.type_username)
async def result_user(message: Message, state: FSMContext):
    await state.clear()
    user = Account(username=message.text.lower(), password=None, active=True).change_token().create()
    if user:
        await message.answer(text=f'User successful created:\n{user.to_bot_message_repr()}', parse_mode='HTML')
    else:
        await message.answer(text=f'User not created:\n User already exist', parse_mode='HTML')


@dp.message(Command('change_status_user'), F.chat.id.in_(ADMIN_TG))
async def change_status_user(message: Message, state: FSMContext) -> None:
    builder = InlineKeyboardBuilder()
    users = Account.filter()
    for user in users:
        builder.add(InlineKeyboardButton(
            text=f'{user.username} {"is_active" if user.active else "is_not_active"}',
            callback_data=user.id)
        )
    await message.answer(text="Select user", reply_markup=builder.as_markup())
    await state.set_state(UserState.status_user)


@dp.callback_query(F.data)
async def result_change_status_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = Account.get(id=callback.data)
    user.active = not user.active
    user.save()
    await callback.message.answer(
        text=f'Status user is successfully change:\n{user.username} {"is_active" if user.active else "is_not_active"}')
    await callback.answer()
