from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


main_menu=InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Kod kiritish", callback_data="code")],
    [InlineKeyboardButton(text="Profilim", callback_data="profile"),InlineKeyboardButton(text="Savat", callback_data="cart")],
    [InlineKeyboardButton(text="DEMO KOD QOSHISH", callback_data="add_test_code")]
])
