-- Создание пользователя и базы проекта. Выполняется один раз под суперпользователем postgres:
--   psql -U postgres -h localhost -f sql/00_create_database.sql
-- Пароль пользователя hh_app запрашивается интерактивно и в файле не хранится.

CREATE ROLE hh_app LOGIN;
\password hh_app

-- template0 + UTF8: русский текст хранится корректно независимо от кодировки Windows
CREATE DATABASE hh_vacancies OWNER hh_app ENCODING 'UTF8' TEMPLATE template0;
