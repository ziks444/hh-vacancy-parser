import argparse
from datetime import datetime
from pathlib import Path

import config
from storage import load_raw
from transform import normalize_vacancy

SCHEMA_FILE = Path(__file__).parent / 'sql' / 'schema.sql'

UPSERT_VACANCY = """
INSERT INTO vacancies (
    id, title, employer, city, address, experience, employment, schedule, working_hours, work_format,
    salary_text, salary_from_rub, salary_to_rub, salary_avg_rub, salary_currency, salary_period, salary_tax,
    published_date, url, query, first_seen_at, last_seen_at
) VALUES (
    %(id)s, %(title)s, %(employer)s, %(city)s, %(address)s, %(experience)s, %(employment)s, %(schedule)s,
    %(working_hours)s, %(work_format)s, %(salary_text)s, %(salary_from_rub)s, %(salary_to_rub)s,
    %(salary_avg_rub)s, %(salary_currency)s, %(salary_period)s, %(salary_tax)s, %(published_date)s,
    %(url)s, %(query)s, %(seen_at)s, %(seen_at)s
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    employer = EXCLUDED.employer,
    city = EXCLUDED.city,
    address = EXCLUDED.address,
    experience = EXCLUDED.experience,
    employment = EXCLUDED.employment,
    schedule = EXCLUDED.schedule,
    working_hours = EXCLUDED.working_hours,
    work_format = EXCLUDED.work_format,
    salary_text = EXCLUDED.salary_text,
    salary_from_rub = EXCLUDED.salary_from_rub,
    salary_to_rub = EXCLUDED.salary_to_rub,
    salary_avg_rub = EXCLUDED.salary_avg_rub,
    salary_currency = EXCLUDED.salary_currency,
    salary_period = EXCLUDED.salary_period,
    salary_tax = EXCLUDED.salary_tax,
    published_date = EXCLUDED.published_date,
    url = EXCLUDED.url,
    query = EXCLUDED.query,
    first_seen_at = LEAST(vacancies.first_seen_at, EXCLUDED.first_seen_at),
    last_seen_at = GREATEST(vacancies.last_seen_at, EXCLUDED.last_seen_at)
"""


def to_db_row(raw, query):
    #Сырая вакансия -> строка таблицы vacancies (+ список навыков отдельно)
    row = normalize_vacancy(raw)

    return {
        'id': int(row['ID']),
        'title': row['Название вакансии'],
        'employer': row['Работодатель'] or None,
        'city': row['Город'],
        'address': row['Адрес'] or None,
        'experience': row['Опыт работы'] or None,
        'employment': row['Занятость'] or None,
        'schedule': row['График работы'] or None,
        'working_hours': row['Рабочие часы'] or None,
        'work_format': row['Формат работы'] or None,
        'salary_text': raw.get('salary_text') or None,
        'salary_from_rub': row['Зарплата (min, руб/мес)'],
        'salary_to_rub': row['Зарплата (max, руб/мес)'],
        'salary_avg_rub': row['Зарплата (avg, руб/мес)'],
        'salary_currency': row['Исходная валюта'] if raw.get('salary_text') else None,
        'salary_period': row['Исходный период'] if raw.get('salary_text') else None,
        'salary_tax': row['Налоги'] or None,
        'published_date': row['Дата публикации'],
        'url': row['Ссылка'],
        'query': query or None,
        'seen_at': row['Дата сбора'] or datetime.now().isoformat(timespec='seconds'),
    }, raw.get('skills') or []


def connect():
    #Подключение по параметрам из .env (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD)
    import psycopg
    from dotenv import load_dotenv

    load_dotenv()
    return psycopg.connect()


def apply_schema(conn):
    conn.execute(SCHEMA_FILE.read_text(encoding='utf-8'))


def save_skills(cur, vacancy_id, skills):
    #Навыки вакансии: новые добавляются в справочник, связи перезаписываются
    cur.execute("DELETE FROM vacancy_skills WHERE vacancy_id = %s", (vacancy_id,))
    for name in dict.fromkeys(s.strip() for s in skills if s and s.strip()):
        cur.execute(
            "INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name RETURNING id",
            (name,))
        skill_id = cur.fetchone()[0]
        cur.execute("INSERT INTO vacancy_skills (vacancy_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (vacancy_id, skill_id))


def load_file(conn, path):
    #Загрузка одного JSON-файла сбора в базу. Возвращает число загруженных вакансий
    query, records = load_raw(path)
    loaded = 0

    with conn.cursor() as cur:
        for raw in records:
            if not raw or not raw.get('id'):
                continue
            row, skills = to_db_row(raw, query)
            cur.execute(UPSERT_VACANCY, row)
            save_skills(cur, row['id'], skills)
            loaded += 1

    conn.commit()
    return loaded


def main():
    parser = argparse.ArgumentParser(description='Загрузка сырых данных сбора в PostgreSQL')
    parser.add_argument('files', nargs='*', help='JSON-файлы сбора (по умолчанию — все из data/raw)')
    args = parser.parse_args()

    files = [Path(f) for f in args.files] or sorted(Path(config.RAW_DIR).glob('*.json'))
    if not files:
        print(f"Нет файлов для загрузки в {config.RAW_DIR}")
        return

    with connect() as conn:
        apply_schema(conn)
        for path in files:
            loaded = load_file(conn, path)
            print(f"{path.name}: загружено {loaded} вакансий")

        total = conn.execute("SELECT count(*) FROM vacancies").fetchone()[0]
        skills = conn.execute("SELECT count(*) FROM skills").fetchone()[0]
        print(f"В базе: {total} вакансий, {skills} навыков")


if __name__ == '__main__':
    main()
