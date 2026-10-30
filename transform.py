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


def is_python_vacancy(title):
    # проверка, что вакансия про пайтон
    if not title:
        return False
    title_lower = title.lower()

    keywords = ['python', 'питон', 'py ', 'py-', 'python developer', 'python engineer', 'django', 'flask', 'fastapi']
    exclude_keywords = ['java ', 'java,', 'javascript', 'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'go ', 'golang']

    for exclude in exclude_keywords:
        if exclude in title_lower:
            return False

    for keyword in keywords:
        if keyword in title_lower:
            return True

    return False


def is_complete_vacancy(data):
    #проверка что поля заполнены
    if not data:
        return False

    if not is_python_vacancy(data['Название вакансии']):
        return False

    if not data['Зарплата (avg, руб/мес)'] or data['Зарплата (текст)'] == 'Не указана':
        return False

    if not data['Опыт работы']:
        return False

    if not data['График работы'] and not data['Занятость']:
        return False

    if not data['Ключевые навыки']:
        return False

    if not data['Название вакансии']:
        return False

    return True
