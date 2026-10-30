import pytest

from transform import (parse_salary, convert_to_rub, convert_to_monthly, vacancy_id_from_url, strip_label,
                       parse_published, city_from_address, detect_tax, normalize_vacancy)


@pytest.mark.parametrize('text, expected', [
    # Вилка в рублях за месяц
    ('от 100 000 до 150 000 ₽ за месяц, до вычета налогов', (100000, 150000, 125000, 'месяц', 'RUB')),
    # Только нижняя граница
    ('от 50 000 ₽ за месяц на руки', (50000, 50000, 50000, 'месяц', 'RUB')),
    # Неразрывные пробелы, как на hh.ru
    ('от\xa0120\xa0000 до\xa0180\xa0000\xa0₽', (120000, 180000, 150000, 'месяц', 'RUB')),
    # Валюта без периода считается месячной
    ('5 000 $', (475000, 475000, 475000, 'месяц', 'USD')),
    ('от 1 000 до 2 000 € за месяц', (103000, 206000, 154500, 'месяц', 'EUR')),
    # Пересчёт периодов в месяц
    ('500 ₽ за час', (84000, 84000, 84000, 'час', 'RUB')),
    ('3 000 ₽ за смену', (66000, 66000, 66000, 'смена', 'RUB')),
    ('10 000 ₽ в неделю', (43000, 43000, 43000, 'неделя', 'RUB')),
])
def test_parse_salary(text, expected):
    assert parse_salary(text) == expected


@pytest.mark.parametrize('text', ['', None, 'Уровень дохода не указан'])
def test_parse_salary_not_specified(text):
    assert parse_salary(text) == (None, None, None, 'месяц', 'RUB')


def test_parse_salary_project_is_skipped():
    assert parse_salary('100 000 ₽ за проект') == (None, None, None, 'проект', 'RUB')


def test_parse_salary_upper_bound_only_is_treated_as_exact():
    # Текущее поведение: «до 150 000» считается фиксированной суммой
    assert parse_salary('до 150 000 ₽ за месяц') == (150000, 150000, 150000, 'месяц', 'RUB')


def test_converters_keep_none():
    assert convert_to_rub(None, 'USD') is None
    assert convert_to_monthly(None, 'час') is None


@pytest.mark.parametrize('url, expected', [
    ('https://hh.ru/vacancy/138800032', '138800032'),
    ('https://hh.ru/vacancy/138800032?query=python', '138800032'),
    ('https://hh.ru/search/vacancy', None),
    (None, None),
])
def test_vacancy_id_from_url(url, expected):
    assert vacancy_id_from_url(url) == expected


@pytest.mark.parametrize('text, label, expected', [
    ('График: 5/2', 'График', '5/2'),
    ('Тип занятости\nПолная занятость', 'Тип занятости', 'Полная занятость'),
    ('Тип занятостиПолная занятость', 'Тип занятости', 'Полная занятость'),
    ('Тип занятости\nПолная занятость\nСтажировка', 'Тип занятости', 'Полная занятость, Стажировка'),
    ('Формат работы: удалённо или гибрид', 'Формат работы', 'удалённо или гибрид'),
    ('Полная занятость', 'Тип занятости', 'Полная занятость'),
    ('', 'График', ''),
    (None, 'График', ''),
])
def test_strip_label(text, label, expected):
    assert strip_label(text, label) == expected


@pytest.mark.parametrize('text, expected', [
    ('Вакансия опубликована 23 октября 2026 в Москве', '2026-10-23'),
    ('Вакансия опубликована 5 марта 2026', '2026-03-05'),
    ('Вакансия опубликована вчера', None),
    ('', None),
])
def test_parse_published(text, expected):
    assert parse_published(text) == expected


@pytest.mark.parametrize('address, expected', [
    ('Москва, Арбатская, Библиотека им.Ленина', 'Москва'),
    ('Санкт-Петербург', 'Санкт-Петербург'),
    ('', None),
    (None, None),
])
def test_city_from_address(address, expected):
    assert city_from_address(address) == expected


@pytest.mark.parametrize('salary_text, salary_type, expected', [
    ('от 50 000 ₽', 'net', 'на руки'),
    ('от 50 000 ₽', 'gross', 'до вычета налогов'),
    ('от 50 000 ₽ за месяц на руки', None, 'на руки'),
    ('от 80 000 ₽ до вычета налогов', None, 'до вычета налогов'),
    ('от 50 000 ₽', None, ''),
    ('', None, ''),
])
def test_detect_tax(salary_text, salary_type, expected):
    assert detect_tax(salary_text, salary_type) == expected


def make_raw(**overrides):
    raw = {
        'id': '138800032',
        'url': 'https://hh.ru/vacancy/138800032',
        'title': 'AI-инженер по автоматизации',
        'employer': 'ООО Атланты',
        'salary_text': 'от 50 000 ₽ за месяц на руки',
        'salary_type': 'net',
        'experience': 'не требуется',
        'employment': 'Тип занятостиПолная занятость',
        'schedule': 'График: 5/2',
        'working_hours': 'Рабочие часы: 8',
        'work_format': 'Формат работы: на месте работодателя или гибрид',
        'skills': ['Python', 'LLM'],
        'address': 'Москва, Арбатская',
        'published_text': 'Вакансия опубликована 23 октября 2026 в Москве',
        'scraped_at': '2026-10-30T15:30:00',
    }
    raw.update(overrides)
    return raw


def test_normalize_vacancy():
    row = normalize_vacancy(make_raw())

    assert row['ID'] == '138800032'
    assert row['Занятость'] == 'Полная занятость'
    assert row['График работы'] == '5/2'
    assert row['Рабочие часы'] == '8'
    assert row['Формат работы'] == 'на месте работодателя или гибрид'
    assert row['Налоги'] == 'на руки'
    assert row['Зарплата (avg, руб/мес)'] == 50000
    assert row['Ключевые навыки'] == 'Python; LLM'
    assert row['Город'] == 'Москва'
    assert row['Дата публикации'] == '2026-10-23'


def test_normalize_vacancy_without_salary():
    row = normalize_vacancy(make_raw(salary_text='', salary_type=None))

    assert row['Зарплата (текст)'] == 'Не указана'
    assert row['Зарплата (avg, руб/мес)'] is None
    assert row['Налоги'] == ''


def test_normalize_vacancy_marks_conversion():
    row = normalize_vacancy(make_raw(salary_text='1 500 $ за месяц', salary_type=None))

    assert row['Зарплата (avg, руб/мес)'] == 142500
    assert 'конвертировано из USD' in row['Зарплата (текст)']


def test_normalize_vacancy_handles_missing_fields():
    row = normalize_vacancy({'id': '1', 'url': 'https://hh.ru/vacancy/1'})

    assert row['Название вакансии'] == ''
    assert row['Ключевые навыки'] == ''
    assert row['Дата публикации'] is None
