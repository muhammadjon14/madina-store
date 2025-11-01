import asyncio
import os
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

class AddCodeStates(StatesGroup):
    waiting_for_code = State()
    waiting_for_images = State()
    waiting_for_description = State()
    waiting_for_quantity = State()

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(f"Assalomu alaykum {message.from_user.full_name}!", reply_markup=main_menu)
    log_action(message.from_user, f"User {message.from_user.id} started the bot.")

@router.callback_query(F.data == "code")
async def enter_code(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Iltimos, kodingizni kiriting:")
    await state.set_state(CodeStates.waiting_for_code)
    await callback.answer()
    log_action(callback.from_user, f"User {callback.from_user.id} is entering a code.")

@router.message(CodeStates.waiting_for_code)
async def check_code(message: Message, state: FSMContext):
    user_code = message.text.strip()
    
    # Validate: Check if code is exactly 4 digits
    if len(user_code) != 4 or not user_code.isdigit():
        await message.answer(f"❌ Kod to'rt xonali raqam bo'lishi kerak. Iltimos, qayta kiriting:")
        log_action(message.from_user, f"User {message.from_user.id} entered invalid code format: {user_code}")
        return
    
    # Check if the code exists in the database
    code_data = database.get_code(user_code)
    
    if code_data:
        code, description, quantity = code_data
        if quantity > 0:
            await message.answer(f"✅ Kod topildi!\n\n📝 Tavsif: {description}\n🔑 Kod: {code}\n🔢 Qoldiq: {quantity} ta\n\nKod mavjud va foydalanishga yaroqli.")
            log_action(message.from_user, f"User {message.from_user.id} entered valid code: {user_code}")
        else:
            await message.answer(f"❌ Bu kod allaqachon tugagan yoki mavjud emas.")
            log_action(message.from_user, f"User {message.from_user.id} entered code with no quantity: {user_code}")
    else:
        await message.answer(f"❌ Kechirasiz, bunday kod topilmadi. Iltimos, kodni qayta tekshirib ko'ring.")
        log_action(message.from_user, f"User {message.from_user.id} entered invalid code: {user_code}")
    
    await state.clear()


@router.callback_query(F.data == "add_test_code")
async def start_add_code(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Iltimos, kodingizni kiriting:")
    await state.set_state(AddCodeStates.waiting_for_code)
    await callback.answer()
    log_action(callback.from_user, f"User {callback.from_user.id} started adding a code.")


@router.message(AddCodeStates.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    user_code = message.text.strip()
    
    # Validate: Check if code is exactly 4 digits
    # Method 1: Using len() and isdigit()
    if len(user_code) != 4 or not user_code.isdigit():
        await message.answer(f"❌ Kod to'rt xonali raqam bo'lishi kerak. Iltimos, qayta kiriting:")
        log_action(message.from_user, f"User {message.from_user.id} tried to add invalid code (not 4 digits): {user_code}")
        # Stay in the same state to ask for code again
        return
    
    # Check if the code already exists
    existing_code = database.get_code(user_code)
    
    if existing_code:
        await message.answer(f"❌ Bu kod allaqachon mavjud. Iltimos, boshqa kod kiriting:")
        log_action(message.from_user, f"User {message.from_user.id} tried to add existing code: {user_code}")
        # Stay in the same state to ask for code again
    else:
        # Code is valid and available, save it and ask for images
        await state.update_data(code=user_code, image_count=0)
        await message.answer(
            "✅ Kod mavjud emas.\n\n"
            "📸 Endi mahsulotning kamida 3 ta rasmini yuboring:\n"
            "(Rasmlarni bitta-bitta yuborishingiz mumkin)"
        )
        await state.set_state(AddCodeStates.waiting_for_images)
        log_action(message.from_user, f"User {message.from_user.id} entered new code: {user_code}")


@router.message(AddCodeStates.waiting_for_images, F.photo)
async def process_images(message: Message, state: FSMContext):
    """Handle image uploads - need at least 3 images"""
    data = await state.get_data()
    code = data.get('code')
    image_count = data.get('image_count', 0)
    
    # Create images directory if it doesn't exist
    images_dir = os.path.join(os.path.dirname(__file__), "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # Get the highest quality photo
    photo = message.photo[-1]
    
    # Save image with format: code1.png, code2.png, etc.
    image_count += 1
    image_filename = f"{code}{image_count}.png"
    image_path = os.path.join(images_dir, image_filename)
    
    # Download and save the image using bot instance
    file = await message.bot.get_file(photo.file_id)
    # Download and save file directly
    await message.bot.download(file, destination=image_path)
    
    # Update state with new image count
    await state.update_data(image_count=image_count)
    
    if image_count < 3:
        # Need more images
        await message.answer(
            f"✅ Rasm {image_count} saqlandi!\n\n"
            f"📸 Yana {3 - image_count} ta rasm yuborishingiz kerak.\n"
            f"(Yoki qo'shimcha rasmlar yuborishingiz mumkin)"
        )
        log_action(message.from_user, f"User {message.from_user.id} uploaded image {image_count} for code {code}")
    else:
        # Have enough images, but allow more
        await message.answer(
            f"✅ Rasm {image_count} saqlandi!\n\n"
            f"✅ Minimal miqdor yuklandi ({image_count} ta rasm)!\n"
            f"📸 Agar kerak bo'lsa, yana rasm yuborishingiz mumkin.\n"
            f"📝 Keyingi bosqichga o'tish uchun matn yuboring."
        )
        log_action(message.from_user, f"User {message.from_user.id} uploaded image {image_count} for code {code}")


@router.message(AddCodeStates.waiting_for_images)
async def process_images_invalid(message: Message, state: FSMContext):
    """Handle non-image messages when waiting for images"""
    data = await state.get_data()
    image_count = data.get('image_count', 0)
    
    if image_count < 3:
        await message.answer(
            f"❌ Iltimos, rasm yuboring!\n\n"
            f"📸 Hozir {image_count} ta rasm yuborildi. Kamida 3 ta rasm kerak."
        )
    else:
        # User sent text, proceed to description
        await message.answer(
            f"✅ {image_count} ta rasm saqlandi!\n\n"
            f"📝 Endi kodning tavsifini kiriting:"
        )
        await state.set_state(AddCodeStates.waiting_for_description)
        log_action(message.from_user, f"User {message.from_user.id} proceeding to description after {image_count} images")


@router.message(AddCodeStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    description = message.text.strip()
    
    # Save description and ask for quantity
    await state.update_data(description=description)
    await message.answer("Endi nechta kod yaratmoqchisiz? (Raqam kiriting):")
    await state.set_state(AddCodeStates.waiting_for_quantity)
    log_action(message.from_user, f"User {message.from_user.id} entered description: {description}")


@router.message(AddCodeStates.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    try:
        quantity = int(message.text.strip())
        
        if quantity <= 0:
            await message.answer("❌ Iltimos, musbat raqam kiriting:")
            return
        
        # Get saved data
        data = await state.get_data()
        code = data.get('code')
        description = data.get('description')
        image_count = data.get('image_count', 0)
        
        # Add single code entry with the specified quantity
        database.add_code(code, description, quantity=quantity)
        
        await message.answer(
            f"✅ Kod muvaffaqiyatli qo'shildi!\n\n"
            f"🔑 Kod: {code}\n"
            f"📝 Tavsif: {description}\n"
            f"📸 Rasmlar: {image_count} ta\n"
            f"🔢 Miqdor: {quantity} ta"
        )
        log_action(message.from_user, f"User {message.from_user.id} added code {code} with {image_count} images, quantity: {quantity}")
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri raqam kiriting:")
        # Stay in the same state to ask for quantity again

