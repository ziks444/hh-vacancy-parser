from load import to_db_row


def make_raw(**overrides):
    raw = {
        'id': '138800032',
        'url': 'https://hh.ru/vacancy/138800032',
        'title': 'AI-инженер по автоматизации',
        'employer': 'ООО Атланты',
        'salary_text': 'от 50 000 ₽ за месяц, на руки',
        'salary_type': 'net',
        'experience': 'не требуется',
        'employment': 'Тип занятости\nПолная занятость',
        'schedule': 'График: 5/2',
        'working_hours': 'Рабочие часы: 8',
        'work_format': 'Формат работы: удалённо',
        'skills': ['Python', 'LLM'],
        'address': 'Москва, Арбатская',
        'published_text': 'Вакансия опубликована 23 октября 2026 в Москве',
        'scraped_at': '2026-10-30T15:30:00',
    }
    raw.update(overrides)
    return raw


def test_to_db_row():
    row, skills = to_db_row(make_raw(), 'аналитик данных')

    assert row['id'] == 138800032
    assert row['employment'] == 'Полная занятость'
    assert row['schedule'] == '5/2'
    assert row['salary_from_rub'] == 50000
    assert row['salary_currency'] == 'RUB'
    assert row['salary_tax'] == 'на руки'
    assert row['city'] == 'Москва'
    assert row['published_date'] == '2026-10-23'
    assert row['query'] == 'аналитик данных'
    assert row['seen_at'] == '2026-10-30T15:30:00'
    assert skills == ['Python', 'LLM']


def test_to_db_row_without_salary_keeps_salary_fields_empty():
    row, _ = to_db_row(make_raw(salary_text='', salary_type=None), '')

    assert row['salary_text'] is None
    assert row['salary_avg_rub'] is None
    assert row['salary_currency'] is None
    assert row['salary_period'] is None
    assert row['salary_tax'] is None
    assert row['query'] is None


def test_to_db_row_empty_strings_become_null():
    row, skills = to_db_row(make_raw(employer='', schedule='', skills=None), 'q')

    assert row['employer'] is None
    assert row['schedule'] is None
    assert skills == []


def test_to_db_row_without_scraped_at_gets_current_time():
    row, _ = to_db_row(make_raw(scraped_at=None), 'q')

    assert row['seen_at']
