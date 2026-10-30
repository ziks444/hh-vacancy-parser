import time
from collections import Counter

import pandas as pd

from config import QUERY, TARGET_COUNT, PAGES, OUTPUT_FILE, USD_TO_RUB, EUR_TO_RUB
from extract import create_driver, collect_vacancy_links, parse_vacancy_page
from transform import is_python_vacancy, is_complete_vacancy
from report import build_excel_report


def main():
    #основной парсинг
    driver = create_driver()
    vacancies = []

    try:
        print(f"Поиск вакансий: {QUERY}")
        print(f"Регион: Москва")
        print(f"Цель: {TARGET_COUNT} вакансий с ПОЛНЫМИ данными")
        print(f"Курсы валют: 1 USD = {USD_TO_RUB} RUB, 1 EUR = {EUR_TO_RUB} RUB")
        print("-" * 60)

        vacancy_links = collect_vacancy_links(driver, QUERY, PAGES)

        print(f"\nВсего найдено ссылок: {len(vacancy_links)}")
        print(f"Парсинг вакансий (нужно {TARGET_COUNT} с полными данными)...")
        print("-" * 60)

        complete_count = 0
        processed_count = 0

        for link in vacancy_links:
            if complete_count >= TARGET_COUNT:
                break

            processed_count += 1
            data = parse_vacancy_page(driver, link)

            if is_complete_vacancy(data):
                vacancies.append(data)
                complete_count += 1
                print(f"[{complete_count}/{TARGET_COUNT}] {data['Название вакансии'][:50]}")
                print(f"      Зарплата: {data['Зарплата (текст)']}")
                print(f"      Валюта: {data['Исходная валюта']}, Период: {data['Исходный период']}")
                print(f"      Опыт: {data['Опыт работы']}")
                print(f"      Навыки: {len(data['Ключевые навыки'].split(';'))} шт.")
            else:
                reasons = []
                if not data:
                    reasons.append("ошибка парсинга")
                elif not is_python_vacancy(data.get('Название вакансии', '')):
                    reasons.append("не Python")
                elif not data.get('Зарплата (avg, руб/мес)'):
                    reasons.append("нет ЗП")
                elif not data.get('Опыт работы'):
                    reasons.append("нет опыта")
                elif not data.get('Ключевые навыки'):
                    reasons.append("нет навыков")
                if reasons:
                    print(f"  Пропущено: {', '.join(reasons)}")

            time.sleep(0.5)

        print("\n" + "=" * 60)
        print(f"Обработано ссылок: {processed_count}")
        print(f"Найдено полных вакансий: {len(vacancies)}")

        periods = [v['Исходный период'] for v in vacancies if v]
        currencies = [v['Исходная валюта'] for v in vacancies if v]
        period_counts = Counter(periods)
        currency_counts = Counter(currencies)

        print(f"Периоды зарплат:")
        for period, count in period_counts.items():
            print(f"  {period}: {count}")
        print(f"Валюты:")
        for curr, count in currency_counts.items():
            print(f"  {curr}: {count}")
        print("=" * 60)

        if len(vacancies) < 5:
            print("ВНИМАНИЕ: Мало данных с полной информацией!")
            return

        df = pd.DataFrame(vacancies)
        build_excel_report(df, currency_counts, period_counts, OUTPUT_FILE)
        print(f"\nФайл сохранен: {OUTPUT_FILE}")

    finally:
        driver.quit()


if __name__ == '__main__':
    main()
