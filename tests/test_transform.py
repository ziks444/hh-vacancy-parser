import pytest

from transform import parse_salary, convert_to_rub, convert_to_monthly, is_python_vacancy, is_complete_vacancy


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


@pytest.mark.parametrize('title, expected', [
    ('Python Developer', True),
    ('Junior Python-разработчик', True),
    ('Backend-разработчик (Django)', True),
    ('Java Developer', False),
    ('Data Analyst', False),
    ('', False),
    # Текущее поведение: исключающее слово важнее ключевого
    ('Fullstack-разработчик (JavaScript, Python)', False),
])
def test_is_python_vacancy(title, expected):
    assert is_python_vacancy(title) == expected


def make_vacancy(**overrides):
    data = {
        'Название вакансии': 'Python Developer',
        'Опыт работы': '1–3 года',
        'График работы': '5/2',
        'Занятость': 'Полная занятость',
        'Зарплата (текст)': 'от 100 000 ₽',
        'Зарплата (avg, руб/мес)': 100000,
        'Ключевые навыки': 'Python; SQL',
    }
    data.update(overrides)
    return data


def test_is_complete_vacancy_accepts_full_data():
    assert is_complete_vacancy(make_vacancy())


@pytest.mark.parametrize('overrides', [
    {'Зарплата (avg, руб/мес)': None},
    {'Зарплата (текст)': 'Не указана'},
    {'Опыт работы': ''},
    {'График работы': '', 'Занятость': ''},
    {'Ключевые навыки': ''},
    {'Название вакансии': 'Java Developer'},
])
def test_is_complete_vacancy_rejects_missing_fields(overrides):
    assert not is_complete_vacancy(make_vacancy(**overrides))


def test_is_complete_vacancy_rejects_none():
    assert not is_complete_vacancy(None)
