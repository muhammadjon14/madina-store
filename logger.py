import logging
import os

class CustomFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = '-'
        if not hasattr(record, 'full_name'):
            record.full_name = '-'
        if not hasattr(record, 'username'):
            record.username = '-'
        if not hasattr(record, 'phone_number'):
            record.phone_number = '-'
        return True

# Logger yaratamiz
logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)
logger.addFilter(CustomFilter())

# Format (millisekundgacha aniqlikda vaqt)
formatter = logging.Formatter(
    "%(asctime)s.%(msecs)03d - LEVEL:%(levelname)s - USER_ID:%(user_id)s - NAME:%(full_name)s - USERNAME:%(username)s - PHONE:%(phone_number)s - MESSAGE:%(message)s",
    "%Y-%m-%d %H:%M:%S"
)

# Konsolga chiqarish
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Faylga yozish
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE_PATH = os.path.join(LOGS_DIR, "bot_logs.log")

file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def log_action(user, action: str, phone_number: str = None):
    """Foydalanuvchi qilgan amallarni log qiladi"""
    extra = {
        "user_id": user.id,
        "full_name": user.full_name,
        "username": f"@{user.username}" if user.username else "None",
        "phone_number": phone_number if phone_number else "-"
    }
    logger.info(action, extra=extra)



def log_system(message: str, level="info"):
    """Bot tizimi loglari (start, error, stop va boshqalar)"""
    extra = {
        "user_id": "-",
        "full_name": "-",
        "username": "-",
        "phone_number": "-"
    }
    if level == "error":
        logger.error(message, extra=extra)
    elif level == "warning":
        logger.warning(message, extra=extra)
    else:
        logger.info(message, extra=extra)
