# 🤖 GeoIP Bot

Бот для определения геолокации IP-адресов, фильтрации и группировки данных. Использует базу данных GeoLite2-City для анализа IP-адресов и предоставляет удобный интерфейс для работы с ними.

Бот развернут на виртуальном частном сервере (VPS) от aeza, что обеспечивает доступность и стабильность работы. Бот работает 24/7, все запросы обрабатываются быстро и эффективно.

Ссылка на бота: [GeoLite2 GeoCity Bot](https://t.me/geolite2geocity_bot)

---

## Содержание

- [Список доступных команд](#список-доступных-команд)
- [Особенности](#особенности)
- [Подробное описание функционала](#подробное-описание-функционала)
  - [1. Определение геолокации по IP-адресам - `/check`](#1-определение-геолокации-по-ip-адресам---check)
  - [2. Определение геолокации с фильтрацией по стране - `/target`](#2-определение-геолокации-с-фильтрацией-по-стране---target)
  - [3. Фильтрация IP-адресов - `/filter`](#3-фильтрация-ip-адресов---filter)
  - [4. Фильтрация IP-адресов по первому октету - `/filter_octet`](#4-фильтрация-ip-адресов-по-первому-октету---filter_octet)
- [Использование](#использование)
  - [Запуск бота](#запуск-бота)
  - [Настройка окружения](#настройка-окружения)
- [Директория проекта](#директория-проекта)

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

## Особенности

- **Определение геолокации**: Группировка IP-адресов по странам и городам.
- **Фильтрация**: Исключение IP-адресов из списков или по первому октету.
- **Кликабельные IP-адреса**: Каждый IP-адрес можно скопировать в буфер обмена нажав на него левой кнопкой мыши.
- **Поддержка ISO-кодов**: Фильтрация IP-адресов по указанной стране.
- **Обновление базы данных**: База данных GeoLite2-City автоматически скачивается и обновляется каждую неделю с официального сайта MaxMind.
- **Обработка нескольких IP-адресов**: Предусмотрена возможность обработки нескольких IP-адресов в одной строке запроса.
- **Сохранение формата запроса**: Содержание и формат каждой строки запроса сохраняются без изменений в текст ответа (для удобства просмотра количества подсетей).
- 
---

## Подробное описание функционала

### 1. Определение геолокации по IP-адресам - /check

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


### 2. Определение геолокации с фильтрацией по стране - /target

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

### 3. Фильтрация IP-адресов - /filter

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

### 4. Фильтрация IP-адресов по первому октету - /filter_octet

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
В requirements.txt указаны библиотеки, необходимые для работы бота.

```bash
pip install -r requirements.txt
```

### Настройка окружения
Перед запуском проекта настройте Python-среду (рекомендуется использовать виртуальное окружение). Затем создайте в корневой директории файл .env и добавьте в него следующие переменные:

```ini
BOT_TOKEN=токен_бота
LICENSE_KEY=ключ_для_GeoLite2
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
