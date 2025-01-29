# справка
help_text = (
        "🤖Справка\n\n"
        "Список доступных команд:\n"
        "/start - начать работу с ботом\n"
        "/help - получить справку\n\n"
        "<b>Проверить страну по IP-адресу</b>\n"
        "1. Введите текст, содержащий IP-адрес(а). Бот проверяет каждую. строку текста и определяет наличие IP-адресов.\n"
        "2. Найденные строки с IP-адресами группируются по странам, а внутри стран — по городам.\n"
        "3. При указании в тексте первыми двумя заглавными латинскими буквами ISO-кода страны (например, \"US\" для США), строки с IP-адресами этой страны будут выведены первыми в результирующем списке.\n"
        "4. Каждый IP-адрес кликабелен — при нажатии копируется в буфер обмена.\n"
        "5. Строки выводятся в том же виде, что в изначальном тексте.\n\n"
        "<b>Пример запроса:</b>\n"
        "\n"
        "US\n"
        "Сервер №36 (35 прокси, 5 подсетей):\n"
        "171.22.76. - 12 прокси\n"
        "102.129.221. - 7 прокси\n"
        "181.214.117. - 6 прокси\n"
        "Сервер №188 (30 прокси, 2 подсетей):\n"
        "195.96.157. - 18 прокси\n"
        "88.216.43. - 12 прокси\n"
        "Сервер №193 (9 прокси, 1 подсетей):\n"
        "176.100.44. - 9 прокси\n"
        "\n\n"
        "<b>Пример ответа:</b>\n"
        "\n"
        "🇺🇸 US (США)\n"
        "Джэксонвилл\n"
        "171.22.76. - 12 прокси\n"
        "Вашингтон\n"
        "102.129.221. - 7 прокси\n"
        "Сакраменто\n"
        "176.100.44. - 9 прокси\n\n"
        "🇦🇪 AE (ОАЭ)\n"
        "Абу-Даби\n"
        "181.214.117. - 6 прокси\n\n"
        "🇸🇨 SC (Сейшельские о-ва)\n"
        "Виктория\n"
        "195.96.157. - 18 прокси\n\n"
        "🇱🇹 LT (Литва)\n"
        "Вильнюс\n"
        "88.216.43. - 12 прокси\n"
        "\n\n"
        "После выполнения этой функции доступна функция <b>\"Отфильтровать IP-адреса по стране\"</b>, "
        "которая выдает в том же формате, что и ранее, все строки с IP-адресами страны, ISO-код которой был введен в тексте запроса.\n"
        "Если в тексте запроса не был указан ISO-код страны, бот выводит все строки, содержащие IP-адреса.\n\n"
        "<b>Отфильтровать IP</b>\n"
        "1. Введите первый текст со списком IP-адресов.\n"
        "2. Введите второй текст со списком IP-адресов, которые нужно исключить из первого списка.\n"
        "3. Бот выведет отфильтрованный список IP-адресов."
    )