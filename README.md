Телеграм-бот для определения геолокации IP-адресов и подсетей
# 🤖 GeoIP Bot

Бот для определения геолокации IP-адресов, фильтрации и группировки данных. Бот использует базу данных **GeoLite2-City** для анализа IP-адресов и предоставляет удобный интерфейс для работы с ними.

---
## Особенности
- **Определение геолокации**: Группировка IP-адресов по странам и городам.
- **Фильтрация**: Исключение IP-адресов из списков или по первому октету.
- **Кликабельные IP-адреса**: Каждый IP-адрес можно скопировать в буфер обмена.
- **Поддержка ISO-кодов**: Фильтрация IP-адресов по указанной стране.
- **Обновление базы данных**: Автоматическая проверка актуальности базы данных GeoLite2-City.
- **Обработка нескольких IP-адресов**: Возможность обработки нескольких IP-адресов в одной строке запроса.
- **Сохранение формата запроса**: Сохранение содержания и формата каждой строки запроса без изменений.

---
## Список доступных команд
### Основные команды:
- `/start` - Начать работу с ботом.
- `/check` - Определить геолокацию по IP-адресам.
- `/target` - Определить геолокацию с фильтрацией по стране.
- `/filter` - Отфильтровать IP-адреса.
- `/filter_octet` - Отфильтровать IP-адреса по первому октету.
- `/help` - Получить справку по использованию бота.
---
## Подробное описание функционала
### 1. Определение геолокации по IP-адресам

1. Введите текст, содержащий IP-адреса.
2. Бот проверяет каждую строку текста и определяет наличие в ней IP-адресов.
3. Найденные строки с IP-адресами группируются по странам, а внутри стран — по городам.
4. Строки выводятся в том же виде, что в изначальном тексте.
5. Внутри строки каждый IP-адрес кликабелен — при нажатии он копируется в буфер обмена.
6. Если в строке больше одного IP-адреса, каждый адрес будет обработан отдельно.

<details>
<summary><b>Пример запроса и ответа</b></summary>

<b>Запрос:</b>

Сервер №36 (35 прокси, 5 подсетей):

171.22.76. - 12 прокси

102.129.221. - 7 прокси

181.214.117. - 6 прокси

Сервер №188 (30 прокси, 2 подсетей):

195.96.157. - 18 прокси

Сервер №193 (9 прокси, 1 подсетей):

<b>Ответ:</b>

🇺🇸 US (США)

Джэксонвилл

171.22.76. - 12 прокси

Вашингтон

102.129.221. - 7 прокси

🇦🇪 AE (ОАЭ)

Абу-Даби

181.214.117. - 6 прокси

🇸🇨 SC (Сейшельские о-ва)

Виктория

195.96.157. - 18 прокси
</details>


### 2. Определение геолокации с фильтрацией по стране

1. Введите текст, содержащий IP-адреса. Первыми двумя заглавными латинскими буквами укажите ISO-код страны
(например, \"US\" для США), IP-адреса которой нужно вывести первыми в ответе на запрос.
2. Бот проверяет каждую строку текста и определяет наличие IP-адресов.
3. Найденные строки с IP-адресами группируются по странам, а внутри стран — по городам.
4. Каждый IP-адрес кликабелен — при нажатии копируется в буфер обмена.
5. IP-адреса страны, ISO-код которой был введен в запросе, будут выведены первыми в результирующем списке.
6. Строки выводятся в том же виде, что в изначальном тексте.
7. В случае, если в одной строке больше одного IP-адреса, каждый адрес будет обработан отдельно.

После выполнения данной функции доступна функция <b>Вывести строки с IP-адресами указанной страны</b>,
которая выдает все строки с IP-адресами страны, ISO-код которой был введен в тексте первого запроса.

<details>
<summary><b>Пример запроса и ответа</b></summary>

<b>Запрос:</b>

NL31.57.176. - 3 прокси

104.234.228. - 2 прокси

31.47.176. - 3 прокси

104.214.228. - 2 прокси

<b>Ответ:</b>

🇳🇱 NL

Амстердам

104.214.228. - 2 прокси


🇺🇸 US (США)

Чикаго

NL31.57.176. - 3 прокси


🇨🇦 CA (Канада)

Оттава

104.234.228. - 2 прокси


🇷🇺 RU (Россия)

Москва

31.47.176. - 3 прокси

Ответ при нажатии кнопки "Вывести строки с IP-адресами указанной страны":

104.214.228. - 2 прокси

</details>

### 3. Фильтрация IP-адресов

1. Введите первый текст со списком IP-адресов.
2. Введите второй текст со списком IP-адресов, которые нужно исключить из первого списка.
3. Бот выведет отфильтрованный список IP-адресов.

<details>
<summary><b>Пример запроса и ответа</b></summary>

<b>Первый запрос:</b>

204.234.228. - 2 прокси

31.47.176. - 3 прокси

115.214.228. - 2 прокси

135.51.88. - 1 прокси

<b>Второй запрос:</b>

204.234.228. - 2 прокси

31.47.176. - 3 прокси

<b>Ответ:</b>

Отфильтрованные IP-адреса:

115.214.228

135.51.88

</details>

### 4. Фильтрация IP-адресов по первому октету
1. Введите первый текст со списком IP-адресов.
2. Введите значение октета - от 1 до 255 включительно.
3. Бот выведет список IP-адресов, исключив те, в которых первый октет равен введенному.

<details>
<summary><b>Пример запроса и ответа</b></summary>

<b>Первый запрос:</b>

204.234.228. - 2 прокси

204.47.176. - 3 прокси

115.214.228. - 2 прокси

135.51.88. - 1 прокси

<b>Второй запрос:</b>

204

Отфильтрованные IP-адреса:

115.214.228

135.51.88

</details>

# Использование

## Запуск бота

Убедитесь, что у вас установлен **Python 3.8+**.

### Установите зависимости:
```bash
pip install -r requirements.txt
```

### Создайте файл `.env` и добавьте туда следующие переменные:
```ini
BOT_TOKEN=ваш_токен_бота
LICENSE_KEY=ваш_ключ_для_GeoLite2
```

### Запустите бота:
```bash
python main.py
```

---

## Директория проекта
```plaintext
project-root/
├── capitals.py          # Логика работы со странами и столицами
├── commands.py          # Обработчики команд бота
├── config.py            # Конфигурация и переменные окружения
├── db_updating.py       # Логика обновления базы данных
├── handlers.py          # Основные обработчики сообщений
├── integration_tests.py # Интеграционные тесты
├── keyboards.py         # Клавиатуры и кнопки
├── main.py              # Точка входа в приложение
├── main_func.py         # Основные функции бота
├── messages.py          # Сообщения бота
├── unit_tests.py        # Юнит-тесты
└── README.md            # Документация проекта
```
---


