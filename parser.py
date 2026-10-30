import argparse
import time
from collections import Counter

import pandas as pd

import config
from report import build_excel_report
from storage import save_raw, load_raw
from transform import normalize_vacancy


def parse_args():
    parser = argparse.ArgumentParser(description='Сбор и анализ вакансий с hh.ru')
    parser.add_argument('--query', default=config.QUERY, help='поисковый запрос')
    parser.add_argument('--pages', type=int, default=config.PAGES, help='сколько страниц поиска пройти')
    parser.add_argument('--max', type=int, default=config.MAX_VACANCIES, help='максимум вакансий')
    parser.add_argument('--from-raw', metavar='PATH',
                        help='не собирать заново, а построить отчёт по сохранённому JSON')
    parser.add_argument('--output', default=config.OUTPUT_FILE, help='имя Excel-файла')
    return parser.parse_args()


def collect(query, pages, max_vacancies):
    #Сбор вакансий через Selenium; сырые данные сохраняются даже при прерывании
    from extract import create_driver, collect_vacancy_links, parse_vacancy_page

    driver = create_driver()
    records = []

    try:
        print(f"Поиск вакансий: {query}")
        print(f"Регион: {config.AREA_NAME}")
        print(f"Не больше {max_vacancies} вакансий, {pages} страниц поиска")
        print("-" * 60)

        vacancy_links = collect_vacancy_links(driver, query, config.AREA_ID, pages,
                                              max_vacancies, config.REQUEST_DELAY)

        print(f"\nВсего найдено ссылок: {len(vacancy_links)}")
        print("-" * 60)

        for num, link in enumerate(vacancy_links, 1):
            data = parse_vacancy_page(driver, link)
            if data:
                records.append(data)
                print(f"[{num}/{len(vacancy_links)}] {data['title'][:50]} | {data['salary_text'] or 'ЗП не указана'}")
            else:
                print(f"[{num}/{len(vacancy_links)}] Пропущено: ошибка парсинга {link}")

            time.sleep(config.REQUEST_DELAY)

    except KeyboardInterrupt:
        print("\nСбор прерван, сохраняю то, что успел собрать...")

    finally:
        driver.quit()
        if records:
            path = save_raw(records, config.RAW_DIR, query)
            print(f"Сырые данные сохранены: {path}")

    return records


def main():
    #основной парсинг
    args = parse_args()

    if args.from_raw:
        query, records = load_raw(args.from_raw)
        query = query or args.query
        print(f"Загружено из {args.from_raw}: {len(records)} вакансий")
    else:
        query = args.query
        records = collect(query, args.pages, args.max)

    if not records:
        print("ВНИМАНИЕ: Не собрано ни одной вакансии!")
        return

    df = pd.DataFrame([normalize_vacancy(r) for r in records])
    with_salary = df[df['Зарплата (avg, руб/мес)'].notna()]

    period_counts = Counter(with_salary['Исходный период'])
    currency_counts = Counter(with_salary['Исходная валюта'])

    print("\n" + "=" * 60)
    print(f"Всего вакансий: {len(df)}")
    print(f"С указанной зарплатой: {len(with_salary)}")
    print(f"Периоды зарплат:")
    for period, count in period_counts.items():
        print(f"  {period}: {count}")
    print(f"Валюты:")
    for curr, count in currency_counts.items():
        print(f"  {curr}: {count}")
    print("=" * 60)

    build_excel_report(df, query, config.AREA_NAME, currency_counts, period_counts, args.output)
    print(f"\nФайл сохранен: {args.output}")


if __name__ == '__main__':
    main()
