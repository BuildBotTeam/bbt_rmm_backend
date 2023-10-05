from aiogram import Dispatcher, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.auth import Account
from models.settings import settings
import re

regex_email = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')

ADMIN_TG = set([int(x) for x in settings.ADMIN_TG.split()])

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()


class UserState(StatesGroup):
    type_username = State()
    type_email = State()
    status_user = State()
    delete_user = State()


@dp.message(CommandStart(), F.chat.id.in_(ADMIN_TG))
async def command_start_handler(message: Message) -> None:
    kb = [
        [KeyboardButton(text="/create_user", )],
        [KeyboardButton(text="/change_status_user")],
        [KeyboardButton(text="/delete_user")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer(f"Hello, {message.from_user.id}!", reply_markup=keyboard)


@dp.message(Command('create_user'), F.chat.id.in_(ADMIN_TG))
async def create_user(message: Message, state: FSMContext) -> None:
    await message.answer(text="Type username")
    await state.set_state(UserState.type_username)


@dp.message(UserState.type_username)
async def type_email(message: Message, state: FSMContext):
    username = message.text.lower()
    await state.clear()
    if username and len(username) > 2:
        user = Account(username=username, password=None, active=True).change_token().create_secret().create()
        if user:
            await message.answer(text=f'User successful created:\n{user.to_bot_message_repr()}', parse_mode='HTML')
        else:
            await message.answer(text=f'User not created:\n User already exist', parse_mode='HTML')


@dp.message(Command('change_status_user'), F.chat.id.in_(ADMIN_TG))
async def change_status_user(message: Message, state: FSMContext) -> None:
    users = Account.filter()
    if not users:
        await message.answer(text="Apps haven't users for this options")
        return await state.clear()
    builder = InlineKeyboardBuilder()
    for user in users:
        builder.row(InlineKeyboardButton(
            text=f'{user.username} {"is_active" if user.active else "is_not_active"}',
            callback_data=user.id)
        )
    builder.row(InlineKeyboardButton(
        text=f'Отмена',
        callback_data='$back')
    )
    await message.answer(text="Select user", reply_markup=builder.as_markup())
    await state.set_state(UserState.status_user)


@dp.callback_query(F.data == '$back')
async def result_change_status_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(text='Отменено')
    await callback.message.delete()
    await state.clear()
    await callback.answer()


@dp.callback_query(UserState.status_user, F.data)
async def result_change_status_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = Account.get(id=callback.data)
    user.active = not user.active
    user.save()
    await callback.message.answer(
        text=f'Status user is successfully change:\n{user.username} {"is_active" if user.active else "is_not_active"}')
    await callback.message.delete()
    await callback.answer()


@dp.message(Command('delete_user'), F.chat.id.in_(ADMIN_TG))
async def change_status_user(message: Message, state: FSMContext) -> None:
    builder = InlineKeyboardBuilder()
    users = Account.filter()
    print(users)
    for user in users:
        builder.row(InlineKeyboardButton(
            text=f'{user.username} {"is_active" if user.active else "is_not_active"}',
            callback_data=user.id)
        )
    builder.row(InlineKeyboardButton(
        text=f'Отмена',
        callback_data='$back')
    )
    await message.answer(text="Select user for DELETE", reply_markup=builder.as_markup())
    await state.set_state(UserState.delete_user)


@dp.callback_query(UserState.delete_user, F.data)
async def result_change_status_user(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user = Account.get(id=callback.data)
    username = user.username
    is_success = user.delete()
    if is_success:
        await callback.message.answer(text=f'{username} successful delete')
    else:
        await callback.message.answer(text=f'{username} delete failed')
    await callback.message.delete()
    await callback.answer()