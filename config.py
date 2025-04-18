import os

from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
LICENSE_KEY = os.getenv('LICENSE_KEY')
TRUSTED_USERS = list(map(lambda x: int(x), os.getenv('TRUSTED_USERS').split(',')))
API_TOKEN = os.getenv('API_TOKEN')
RESTRICT_ACCESS = os.getenv('RESTRICT_ACCESS') if os.getenv('RESTRICT_ACCESS') else False
ADMIN_ID = os.getenv('ADMIN_ID')
NOTIFY_ADMIN = False
bot = Bot(token=BOT_TOKEN)
database_filename = 'GeoLite2-City.mmdb'
url = (
    f"https://download.maxmind.com/app/geoip_download?"
    f"edition_id=GeoLite2-City&license_key={LICENSE_KEY}"
    f"&suffix=tar.gz"
)

# регулярное выражение для поиска подсетей и IP-адресов
pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|(?<![\d\.])\d{1,3}\.\d{1,3}\.\d{1,3}(?!\.\d)"
pattern_ping = r"^(https?:\/\/)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z0-9-]+$|^(?:\d{1,3}\.){3}\d{1,3}$"

# хранение логгеров всех пользователей
user_loggers = {}

# переменная для хранения списка IP-адресов
user_data = {}