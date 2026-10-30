import re

from config import USD_TO_RUB, EUR_TO_RUB, HOURS_PER_MONTH, DAYS_PER_MONTH, WEEKS_PER_MONTH


def detect_salary_period(text):
    #Определение периода зарплаты из текста
    text_lower = text.lower()

    if 'за час' in text_lower or 'в час' in text_lower or '/час' in text_lower:
        return 'час'
    elif 'за день' in text_lower or 'в день' in text_lower or '/день' in text_lower:
        return 'день'
    elif 'за смену' in text_lower or 'в смену' in text_lower:
        return 'смена'
    elif 'за неделю' in text_lower or 'в неделю' in text_lower:
        return 'неделя'
    elif 'за месяц' in text_lower or 'в месяц' in text_lower:
        return 'месяц'
    elif 'за проект' in text_lower:
        return 'проект'
    else:
        return 'месяц'


def detect_currency(text):
    #Определение валюты зарплаты
    text_lower = text.lower()

    if '$' in text or 'usd' in text_lower or 'долл' in text_lower:
        return 'USD'
    elif '€' in text or 'eur' in text_lower or 'евро' in text_lower:
        return 'EUR'
    else:
        return 'RUB'


def convert_to_monthly(value, period):
    #Приведение зарплаты к месячному эквиваленту
    if value is None:
        return None

    if period == 'час':
        return value * HOURS_PER_MONTH
    elif period == 'день':
        return value * DAYS_PER_MONTH
    elif period == 'смена':
        return value * DAYS_PER_MONTH
    elif period == 'неделя':
        return int(value * WEEKS_PER_MONTH)
    elif period == 'месяц':
        return value
    elif period == 'проект':
        return None

    return value


def convert_to_rub(value, currency):
    #Конвертация валюты в рубли
    if value is None:
        return None

    if currency == 'USD':
        return int(value * USD_TO_RUB)
    elif currency == 'EUR':
        return int(value * EUR_TO_RUB)
    return value


def parse_salary(text):
    #Парсинг суммы зарплаты с конвертацией в рубли и приведением к месячной
    if not text or 'не указан' in text.lower():
        return None, None, None, 'месяц', 'RUB'

    period = detect_salary_period(text)
    currency = detect_currency(text)

    if period == 'проект':
        return None, None, None, 'проект', currency

    # Удаление лишнего текста
    clean_text = text.lower()
    for word in ['за час', 'в час', '/час', 'за день', 'в день', '/день',
                 'за смену', 'в смену', 'за неделю', 'в неделю',
                 'за месяц', 'в месяц', 'за проект']:
        clean_text = clean_text.replace(word, '')

    # Очистка символов валют и слов
    clean_text = clean_text.replace('$', '').replace('€', '')
    for word in ['usd', 'eur', 'руб', 'рублей', 'доллар', 'долларов', 'евро']:
        clean_text = clean_text.replace(word, '')

    clean_text = clean_text.replace(' ', '').replace('₽', '').replace('\xa0', '')
    nums = re.findall(r'\d+', clean_text)

    if not nums:
        return None, None, None, period, currency

    if len(nums) == 1:
        val = int(nums[0])
        val_rub = convert_to_rub(val, currency)
        monthly_val = convert_to_monthly(val_rub, period)
        return monthly_val, monthly_val, monthly_val, period, currency

    min_val = int(nums[0])
    max_val = int(nums[1])
    min_rub = convert_to_rub(min_val, currency)
    max_rub = convert_to_rub(max_val, currency)
    monthly_min = convert_to_monthly(min_rub, period)
    monthly_max = convert_to_monthly(max_rub, period)
    monthly_avg = (monthly_min + monthly_max) // 2

    return monthly_min, monthly_max, monthly_avg, period, currency


MONTHS = {
    'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4, 'мая': 5, 'июня': 6,
    'июля': 7, 'августа': 8, 'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12,
}


def vacancy_id_from_url(url):
    #ID вакансии из ссылки вида https://hh.ru/vacancy/123456
    match = re.search(r'/vacancy/(\d+)', url or '')
    return match.group(1) if match else None


def strip_label(text, label):
    #Удаление подписи поля, например «График: 5/2» -> «5/2»
    text = (text or '').strip()
    if text.lower().startswith(label.lower()):
        text = text[len(label):]
    # Несколько значений приходят построчно: «Полная занятость\nСтажировка»
    lines = [line.strip() for line in text.strip(' :\n').split('\n')]
    return ', '.join(line for line in lines if line)


def parse_published(text):
    #«Вакансия опубликована 23 октября 2026 в Москве» -> '2026-10-23'
    match = re.search(r'опубликована\s+(\d{1,2})\s+([а-я]+)\s+(\d{4})', text or '')
    if not match or match.group(2) not in MONTHS:
        return None

    day, month, year = int(match.group(1)), MONTHS[match.group(2)], int(match.group(3))
    return f'{year:04d}-{month:02d}-{day:02d}'


def city_from_address(address):
    #«Москва, Арбатская, ...» -> «Москва»
    city = (address or '').split(',')[0].strip()
    return city or None


def detect_tax(salary_text, salary_type=None):
    #На руки или до вычета налогов
    if salary_type == 'net':
        return 'на руки'
    if salary_type == 'gross':
        return 'до вычета налогов'

    text_lower = (salary_text or '').lower()
    if 'на руки' in text_lower:
        return 'на руки'
    if 'до вычета' in text_lower:
        return 'до вычета налогов'
    return ''


def normalize_vacancy(raw):
    #Приведение сырой записи к строке таблицы: зарплата в рублях/месяц, поля без подписей
    salary_text = raw.get('salary_text') or ''
    s_min, s_max, s_avg, period, currency = parse_salary(salary_text)

    # Пометка, что произведен пересчет
    salary_note = salary_text or 'Не указана'
    notes = []
    if currency != 'RUB':
        notes.append(f'конвертировано из {currency}')
    if period != 'месяц' and period != 'проект' and s_avg is not None:
        notes.append(f'пересчитано с {period}а')
    if notes:
        salary_note = f"{salary_text} ({'; '.join(notes)})"

    return {
        'ID': raw.get('id'),
        'Название вакансии': raw.get('title', ''),
        'Работодатель': raw.get('employer', ''),
        'Опыт работы': raw.get('experience', ''),
        'Занятость': strip_label(raw.get('employment'), 'Тип занятости'),
        'График работы': strip_label(raw.get('schedule'), 'График'),
        'Рабочие часы': strip_label(raw.get('working_hours'), 'Рабочие часы'),
        'Формат работы': strip_label(raw.get('work_format'), 'Формат работы'),
        'Зарплата (текст)': salary_note,
        'Налоги': detect_tax(salary_text, raw.get('salary_type')),
        'Исходная валюта': currency,
        'Исходный период': period,
        'Зарплата (min, руб/мес)': s_min,
        'Зарплата (max, руб/мес)': s_max,
        'Зарплата (avg, руб/мес)': s_avg,
        'Ключевые навыки': '; '.join(raw.get('skills') or []),
        'Город': city_from_address(raw.get('address')),
        'Адрес': raw.get('address', ''),
        'Дата публикации': parse_published(raw.get('published_text')),
        'Дата сбора': raw.get('scraped_at'),
        'Ссылка': raw.get('url'),
    }
