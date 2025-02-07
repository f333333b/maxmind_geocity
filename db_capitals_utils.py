import asyncpg
from capitals import capitals

async def get_capital(country_en):
    async with db_pool.acquire() as conn:
        return await conn.fetch(
        """
        SELECT capital_name FROM capitals
        WHERE country_name = %1
        """, country_en)

async def init_db_pool():
    """Создание пула соединений для работы с БД"""
    global db_pool
    db_pool = await asyncpg.create_pool(
        user='postgres',
        password='1',
        database='postgres',
        host='localhost',
        port='5432'
    )

async def check_db_connection():
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetch("SELECT 1")
            if result:
                print("Соединение с базой данных установлено!")
    except Exception as e:
        print(f"Ошибка соединения с базой данных: {e}")

async def insert_capitals(capitals):
    try:
        async with db_pool.acquire() as conn:
            for country, capital in capitals.items():
                await conn.execute(
                    "INSERT INTO capitals (country_name, capital_name) VALUES ($1, $2)",
                    country, capital
                )
            print("Данные успешно внесены в таблицу.")
    except Exception as e:
        print(f"Ошибка при внесении данных: {e}")

async def main():
    await init_db_pool()
    await check_db_connection()
    await insert_capitals(capitals)