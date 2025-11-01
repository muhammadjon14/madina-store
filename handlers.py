import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from button import main_menu
import database
from logger import log_action
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()
class CodeStates(StatesGroup):
    waiting_for_code = State()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Assalomu alaykum !", message.from_user.full_name, reply_markup=main_menu)
    log_action(f"User {message.from_user.id} started the bot.")

@router.callback_query(F.data == "code")
async def enter_code(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Iltimos, kodingizni kiriting:")
    await state.set_state(CodeStates.waiting_for_code)
    await callback.answer()
    log_action(f"User {callback.from_user.id} is entering a code.")

@router.message(CodeStates.waiting_for_code)
async def check_code(message: Message, state: FSMContext):
    user_code = message.text.strip()
    
    # Check if the code exists in the database
    code_data = database.get_code(user_code)
    
    if code_data:
        code, description, availability = code_data
        if availability == 11:
            await message.answer(f"✅ Kod topildi!\n\n📝 Tavsif: {description}\n🔑 Kod: {code}\n\nKod mavjud va foydalanishga yaroqli.")
            log_action(f"User {message.from_user.id} entered valid code: {user_code}")
        else:
            await message.answer(f"❌ Bu kod allaqachon ishlatilgan yoki mavjud emas.")
            log_action(f"User {message.from_user.id} entered used/unavailable code: {user_code}")
    else:
        await message.answer(f"❌ Kechirasiz, bunday kod topilmadi. Iltimos, kodni qayta tekshirib ko'ring.")
        log_action(f"User {message.from_user.id} entered invalid code: {user_code}")
    
    await state.clear()

