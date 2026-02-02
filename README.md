# ValutaTrade Hub

Консольное приложение для работы с валютами и портфелем пользователя.

## Назначение проекта

Проект реализует базовый набор операций:
- регистрация пользователя и управление сессией (вход/выход);
- хранение портфеля пользователя;
- операции покупки и продажи валюты;
- получение курса валют (включая кросс-курс при необходимости);
- получение курса валют (в т.ч. кросс-курс при необходимости);
- обновление курсов из внешних источников и сохранение в локальный кеш;
- просмотр курсов из кеша с фильтрами.

## Технологии

- Python 3.12+
- Poetry (установка и запуск)
- Ruff (проверка стиля)
- unittest (тестирование)

## Установка и запуск

1) Клонировать репозиторий и перейти в папку проекта:

2) Установить зависимости:

    poetry install

3) Проверить качество кода:

    make lint

4) Запустить тесты:

    poetry run python -m unittest -q

## Переменные окружения

Для источника ExchangeRate-API требуется ключ:

- EXCHANGERATE_API_KEY - API key для ExchangeRate-API

Пример установки переменной:

    export EXCHANGERATE_API_KEY="ваш_ключ"

Если ключ не задан, обновление курсов будет выполнено частично: данные ExchangeRate-API будут недоступны, но другие источники могут отработать успешно.

## Команды CLI

Команды запускаются через Poetry.

Общая справка:

    poetry run project -h

Доступные команды:
- register - регистрация пользователя
- login - вход пользователя
- logout - выход (сброс сессии)
- get-rate - получить курс валют
- buy - купить валюту
- sell - продать валюту
- show-portfolio - показать портфель пользователя
- update-rates - обновить курсы (parser_service)
- show-rates - показать курсы из локального кеша

### register

    poetry run project register <username> <password>

### login

    poetry run project login <username> <password>

### logout

    poetry run project logout

### get-rate

Команда использует позиционные аргументы:

    poetry run project get-rate <FROM> <TO>

Примеры:

    poetry run project get-rate EUR USD
    poetry run project get-rate USD RUB
    poetry run project get-rate BTC USD

### buy

    poetry run project buy <CURRENCY_CODE> <AMOUNT>

Пример:

    poetry run project buy EUR 10

### sell

    poetry run project sell <CURRENCY_CODE> <AMOUNT>

Пример:

    poetry run project sell EUR 5

### show-portfolio

    poetry run project show-portfolio

### update-rates

    poetry run project update-rates

Выбор источника:

    poetry run project update-rates --source all
    poetry run project update-rates --source coingecko
    poetry run project update-rates --source exchangerate

Примечания:
- coingecko - источник криптовалют (например BTC/ETH/SOL к USD)
- exchangerate - источник фиатных валют (например EUR/GBP/RUB к USD), требует EXCHANGERATE_API_KEY
- all - обновление из всех доступных источников

### show-rates

    poetry run project show-rates

Опции:
- --currency - показать курс только для валюты (например, BTC)
- --top - показать N самых больших значений по rate
- --base - базовая валюта для вывода (USD по умолчанию)

Примеры:

    poetry run project show-rates
    poetry run project show-rates --top 3
    poetry run project show-rates --currency BTC
    poetry run project show-rates --base EUR --top 5

## Хранение данных

Рабочие данные приложения сохраняются в директории data/. Эти файлы являются runtime-данными и не должны коммититься в репозиторий.

Типовые файлы:
- data/users.json - данные зарегистрированных пользователей
- data/session.json - текущая сессия (кто вошел)
- data/portfolios.json - портфели пользователей
- data/rates.json - кеш курсов валют

Формат data/rates.json:
- pairs - словарь пар в виде FROM_TO -> {rate, updated_at, source}
- last_refresh - время последнего обновления

## Логи

Логи сохраняются в директории logs/ (runtime-данные, не коммитятся).
Основной файл логов обновления курсов:
- logs/parser_service.log

## Демонстрация (asciinema)

- регистрация и вход пользователя;
- обновление курсов;
- просмотр курсов (обычный вывод и с фильтрами);
- получение курса;
- покупка/продажа;
- просмотр портфеля;
- выход из сессии.

Запись терминала: [docs/asciinema.cast](docs/asciinema.cast)

