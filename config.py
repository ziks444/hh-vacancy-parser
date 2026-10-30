#Параметры поиска (можно переопределить аргументами командной строки)
QUERY = "Python Developer"
AREA_ID = 1  # 1 — Москва
AREA_NAME = 'Москва'
PAGES = 5
MAX_VACANCIES = 200

#Пауза между запросами к hh.ru, сек — чтобы не создавать лишнюю нагрузку
REQUEST_DELAY = 1.0

#Куда сохранять результаты
RAW_DIR = 'data/raw'
OUTPUT_FILE = 'vacancies_moscow.xlsx'

#Курсы для конвертации в рубли
USD_TO_RUB = 95.0
EUR_TO_RUB = 103.0

#К/Ф для приведения к месячной заработной плате
HOURS_PER_MONTH = 168
DAYS_PER_MONTH = 22
WEEKS_PER_MONTH = 4.3
