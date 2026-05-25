# Gift Advisor Bot — пошаговая инструкция / Setup guide

Бот для рекомендации подарков на Telegram. Использует Grok LLM (xAI) и сравнивает 4 стратегии prompt engineering.

---

## 📋 Что нужно перед началом / Prerequisites

1. **Python 3.11 или новее** ([скачать](https://www.python.org/downloads/))
2. **Аккаунт Telegram** (на любом телефоне)
3. **Аккаунт на console.x.ai** для получения Grok API key (платно, ~$5-10 хватит для всех тестов)

---

## 🚀 Шаг 1. Скачать и установить / Install

Открой терминал (PowerShell на Windows, Terminal на Mac) и выполни команды по очереди:

```bash
# 1. Зайди в папку проекта
cd path/to/bot_project

# 2. Создай виртуальное окружение
python -m venv .venv

# 3. Активируй его
# Windows:
.venv\Scripts\activate
# Mac / Linux:
source .venv/bin/activate

# 4. Установи библиотеки
pip install -r requirements.txt
```

Если всё прошло без ошибок, ты должна увидеть в начале строки терминала `(.venv)`.

---

## 🔑 Шаг 2. Получить Telegram Bot Token

1. Открой Telegram, найди **@BotFather**.
2. Напиши ему `/newbot`.
3. Выбери имя бота (например, `My Gift Advisor`).
4. Выбери username (должен заканчиваться на `bot`, например `my_gift_advisor_bot`).
5. BotFather пришлёт токен вида `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`.
6. **Скопируй этот токен. Он будет нужен на следующем шаге.**

---

## 🔑 Шаг 3. Получить Grok API Key

1. Зайди на https://console.x.ai
2. Зарегистрируйся (можно через Google).
3. Положи $5–10 на баланс (карта международная).
4. Перейди в раздел **API Keys** → **Create API Key**.
5. **Скопируй ключ.** Он начинается с `xai-...`.

---

## ⚙️ Шаг 4. Создать файл .env

В папке проекта есть файл `.env.example`. Скопируй его в `.env`:

```bash
# Windows:
copy .env.example .env
# Mac / Linux:
cp .env.example .env
```

Открой `.env` в текстовом редакторе (Notepad, VS Code) и впиши свои реальные ключи:

```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
GROK_API_KEY=xai-abc123def456...
GROK_MODEL=grok-2-latest
DEFAULT_STRATEGY=cot
```

**⚠️ Не показывай этот файл никому и не загружай его на GitHub!**

---

## ▶️ Шаг 5. Запустить бота

```bash
python bot.py
```

Должно появиться:
```
INFO:__main__:Bot is starting...
INFO:aiogram.dispatcher:Start polling
```

Бот работает! Открой Telegram, найди своего бота по username (например `@my_gift_advisor_bot`), и нажми **Start**.

---

## 📸 Шаг 6. Сделать скриншоты для диплома

Тебе нужны 6–8 скриншотов:

1. **Welcome screen** — экран после `/start` (для Figure 3.1)
2. **Question 1: relation** — 4 кнопки (Friend / Family / Partner / Colleague)
3. **Question 6: interests** — multi-select с галочками
4. **Free text step** — экран запроса дополнительного текста
5. **"Thinking..."** — экран ожидания ответа Grok
6. **3 gift ideas** — финальные рекомендации (самый важный скриншот!)
7. **Rating step** — кнопки 1–5
8. **`/my` command** — список предыдущих сессий

Положи их в папку диплома: `b_chapters/chapter3/screenshots/`

---

## 🧪 Шаг 7. Запустить эксперимент (30 персон × 4 стратегии = 120 кейсов)

```bash
python -m experiment.run_experiment
```

Это займёт около **30 минут** (120 запросов с паузой 1 секунда + время ответа Grok).
Стоимость: примерно **$3–5** в зависимости от модели.

Результаты сохраняются в `experiment/results.json` и `experiment/results.csv`.

---

## 📊 Шаг 8. Оценить результаты вручную

```bash
python -m experiment.make_scoring_sheet
```

Это создаст файл `experiment/scoring_sheet.csv`. Открой его в **Excel** или **Google Sheets**.

Для каждой строки оцени:
- **relevance_1_5** — насколько подарок подходит профилю (1–5)
- **creativity_1_5** — оригинальность, отсутствие клише (1–5)
- **specificity_1_5** — конкретность предложения (1–5)
- **hallucination_count_0_3** — сколько из 3 идей не существуют на рынке (0, 1, 2 или 3)

⚠️ Это самая долгая часть — около 2–3 часов внимательной работы. Но без неё нет научной части диплома.

После заполнения **сохрани** файл (Save) и запусти:

```bash
python -m experiment.analyze
```

Это выведет итоговую таблицу и сохранит её в `experiment/summary.csv`. Эти числа пойдут в Chapter 3.2 (Results) диплома.

---

## 🆘 Если что-то не работает

### "ModuleNotFoundError: No module named 'aiogram'"
Не активирована виртуальная среда. Выполни `source .venv/bin/activate` (Mac) или `.venv\Scripts\activate` (Windows).

### "BOT_TOKEN is missing"
Проверь, что файл `.env` создан и содержит реальный токен.

### "401 Unauthorized" от Grok
Проверь GROK_API_KEY и баланс на console.x.ai.

### Бот не отвечает в Telegram
Проверь, что в терминале запущен `python bot.py` и нет ошибок.

---

## 📁 Структура проекта

```
bot_project/
├── bot.py                 # main entry point, всё про FSM и обработку команд
├── database.py            # SQLite, 3 таблицы
├── grok_client.py         # асинхронный клиент к Grok API
├── prompts/
│   ├── __init__.py
│   └── builder.py         # 4 стратегии (naive, constrained, cot, persona)
├── experiment/
│   ├── personas.json      # 30 синтетических персон
│   ├── run_experiment.py  # запуск 120 кейсов
│   ├── make_scoring_sheet.py  # подготовка таблицы оценки
│   └── analyze.py         # подсчёт итогов
├── requirements.txt
├── .env.example           # шаблон для .env
├── .gitignore
└── README.md              # этот файл
```
