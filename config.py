import os
from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
LICENSE_KEY = os.getenv('LICENSE_KEY')
bot = Bot(token=TOKEN)
database_filename = 'GeoLite2-City.mmdb'
url = (
    f"https://download.maxmind.com/app/geoip_download?"
    f"edition_id=GeoLite2-City&license_key={LICENSE_KEY}"
    f"&suffix=tar.gz"
)

# регулярное выражение для поиска подсетей и IP-адресов
pattern = r"\d+\.\d+\.\d+\.\d+|(?<![\d\.])\d+\.\d+\.\d+(?!\.\d)"

# отслеживание состояния пользователя
user_states = {}
user_data = {}

# переменная для хранения IP-адресов
user_ips = {}

# хранение логгеров всех пользователей
user_loggers = {}