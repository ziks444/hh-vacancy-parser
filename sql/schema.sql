-- Схема базы вакансий. Скрипт можно запускать повторно: объекты создаются, только если их нет.

CREATE TABLE IF NOT EXISTS vacancies (
    id              BIGINT PRIMARY KEY,         -- ID вакансии на hh.ru
    title           TEXT NOT NULL,
    employer        TEXT,
    city            TEXT,
    address         TEXT,
    experience      TEXT,                       -- «не требуется», «1–3 года», ...
    employment      TEXT,                       -- «Полная занятость», ...
    schedule        TEXT,                       -- «5/2», ...
    working_hours   TEXT,
    work_format     TEXT,                       -- «удалённо», «гибрид», ...
    salary_text     TEXT,                       -- зарплата как на сайте
    salary_from_rub INTEGER,                    -- в рублях за месяц
    salary_to_rub   INTEGER,
    salary_avg_rub  INTEGER,
    salary_currency TEXT,                       -- исходная валюта: RUB, USD, EUR
    salary_period   TEXT,                       -- исходный период: месяц, час, ...
    salary_tax      TEXT,                       -- «на руки», «до вычета налогов» или NULL
    published_date  DATE,
    url             TEXT NOT NULL,
    query           TEXT,                       -- поисковый запрос, которым вакансия найдена
    first_seen_at   TIMESTAMP NOT NULL,         -- когда впервые попала в сбор
    last_seen_at    TIMESTAMP NOT NULL          -- когда последний раз попала в сбор
);

CREATE TABLE IF NOT EXISTS skills (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Связь «многие ко многим»: у вакансии много навыков, навык встречается во многих вакансиях
CREATE TABLE IF NOT EXISTS vacancy_skills (
    vacancy_id BIGINT  NOT NULL REFERENCES vacancies (id) ON DELETE CASCADE,
    skill_id   INTEGER NOT NULL REFERENCES skills (id) ON DELETE CASCADE,
    PRIMARY KEY (vacancy_id, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_vacancies_published_date ON vacancies (published_date);
CREATE INDEX IF NOT EXISTS idx_vacancies_salary_avg ON vacancies (salary_avg_rub);
CREATE INDEX IF NOT EXISTS idx_vacancy_skills_skill ON vacancy_skills (skill_id);
