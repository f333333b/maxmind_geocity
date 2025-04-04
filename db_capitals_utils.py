import asyncpg

async def get_capital(country_en):
    """Функция обращения к базе данных capitals для получения столицы страны"""
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow(
            """
            SELECT capital FROM capitals
            WHERE country = $1
            """, country_en)
        if result:
            return result['capital']
        else:
            return "Неизвестно"

async def init_db_pool():
    """Функция создания пула соединений для работы с базой данных"""
    global db_pool
    db_pool = await asyncpg.create_pool(
        user='postgres',
        password='1',
        database='postgres',
        host='localhost',
        port='5432'
    )

async def get_db_pool():
    """Функция для безопасного получения db_pool"""
    if db_pool is None:
        raise RuntimeError("Ошибка: db_pool не инициализирован! Вызовите init_db_pool() перед использованием.")
    return db_pool

async def check_db_connection():
    """Функция проверки соединения с базой данных PostgreSQL"""
    try:
        async with db_pool.acquire() as conn:
            result = await conn.fetch("SELECT 1")
            if result:
                print("Соединение с базой данных capitals успешно установлено")
    except Exception as e:
        print(f"Ошибка соединения с базой данных capitals: {e}")

async def insert_capitals(capitals):
    """Функция внесения информации из словаря в базу данных capitals"""
    try:
        async with db_pool.acquire() as conn:
            # удаление таблицы
            await conn.execute(
                "DROP TABLE IF EXISTS capitals CASCADE;")

            # создание таблицы
            await conn.execute(
                "CREATE TABLE capitals ("
                "country VARCHAR, "
                "capital VARCHAR, "
                "ISO VARCHAR);"
            )

            # наполнение таблицы
            for country, data in capitals.items():
                await conn.execute(
                    "INSERT INTO capitals (country, capital, ISO) VALUES ($1, $2, $3)",
                    country, data[0], data[1]
                )
            print("Данные успешно внесены в таблицу.")
    except Exception as e:
        print(f"Ошибка при внесении данных: {e}")