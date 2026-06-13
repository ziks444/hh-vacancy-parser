from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import re
import io
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from collections import Counter

#Курсы для конвертации в рубли
USD_TO_RUB = 95.0
EUR_TO_RUB = 103.0

#К/Ф для приведения к месячной заработной плате
HOURS_PER_MONTH = 168
DAYS_PER_MONTH = 22
WEEKS_PER_MONTH = 4.3


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


def parse_vacancy_page(driver, url):
    #Парсинг одной страницы вакансии
    data = {
        'Название вакансии': '',
        'Опыт работы': '',
        'График работы': '',
        'Занятость': '',
        'Зарплата (текст)': '',
        'Исходная валюта': '',
        'Исходный период': '',
        'Зарплата (min, руб/мес)': None,
        'Зарплата (max, руб/мес)': None,
        'Зарплата (avg, руб/мес)': None,
        'Ключевые навыки': '',
        'Регион': 'Москва'
    }

    try:
        driver.get(url)
        time.sleep(1)

        try:
            title = driver.find_element(By.CSS_SELECTOR, "[data-qa='vacancy-title']")
            data['Название вакансии'] = title.text.strip()
        except:
            pass

        try:
            salary = driver.find_element(By.CSS_SELECTOR, "[data-qa='vacancy-salary']")
            salary_text = salary.text.strip()
            data['Зарплата (текст)'] = salary_text

            s_min, s_max, s_avg, period, currency = parse_salary(salary_text)
            data['Исходный период'] = period
            data['Исходная валюта'] = currency
            data['Зарплата (min, руб/мес)'] = s_min
            data['Зарплата (max, руб/мес)'] = s_max
            data['Зарплата (avg, руб/мес)'] = s_avg

            # Пометка, что произведен пересчет
            notes = []
            if currency != 'RUB':
                notes.append(f'конвертировано из {currency}')
            if period != 'месяц' and period != 'проект' and s_avg is not None:
                notes.append(f'пересчитано с {period}а')
            if notes:
                data['Зарплата (текст)'] = f"{salary_text} ({'; '.join(notes)})"
        except:
            data['Зарплата (текст)'] = 'Не указана'
            data['Исходный период'] = 'месяц'
            data['Исходная валюта'] = 'RUB'

        try:
            exp = driver.find_element(By.CSS_SELECTOR, "[data-qa='vacancy-experience']")
            data['Опыт работы'] = exp.text.strip()
        except:
            pass

        try:
            schedule = driver.find_element(By.CSS_SELECTOR, "[data-qa='work-schedule-by-days-text']")
            data['График работы'] = schedule.text.strip()
        except:
            pass

        try:
            employment = driver.find_element(By.CSS_SELECTOR, "[data-qa='common-employment-text']")
            data['Занятость'] = employment.text.strip()
        except:
            pass

        try:
            skill_elements = driver.find_elements(By.CSS_SELECTOR, "[data-qa='skills-element']")
            skills_list = []
            for skill_el in skill_elements:
                try:
                    skill_div = skill_el.find_element(By.CSS_SELECTOR, "div[class*='magritte-tag']")
                    skill_text = skill_div.text.strip()
                    if skill_text:
                        skills_list.append(skill_text)
                except:
                    skill_text = skill_el.text.strip()
                    if skill_text:
                        skills_list.append(skill_text)
            data['Ключевые навыки'] = '; '.join(skills_list[:10])
        except:
            pass

        return data
    except:
        return None


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


def main():
    #основной парсинг
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=options)
    vacancies = []

    try:
        query = "Python Developer"
        target_count = 10
        pages = 10

        print(f"Поиск вакансий: {query}")
        print(f"Регион: Москва")
        print(f"Цель: {target_count} вакансий с ПОЛНЫМИ данными")
        print(f"Курсы валют: 1 USD = {USD_TO_RUB} RUB, 1 EUR = {EUR_TO_RUB} RUB")
        print("-" * 60)

        vacancy_links = []

        for page in range(pages):
            url = f"https://hh.ru/search/vacancy?text={query.replace(' ', '+')}&area=1&page={page}"
            print(f"Сбор ссылок: страница {page + 1}/{pages}...")

            driver.get(url)
            time.sleep(1.5)

            try:
                buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Понятно')]")
                if buttons:
                    buttons[0].click()
                    time.sleep(0.5)
            except:
                pass

            try:
                links = driver.find_elements(By.CSS_SELECTOR, "a[data-qa='serp-item__title']")
                page_python_count = 0
                for link in links:
                    href = link.get_attribute('href')
                    title_text = link.text.strip()
                    if href and 'hh.ru/vacancy/' in href and href not in vacancy_links:
                        if is_python_vacancy(title_text):
                            vacancy_links.append(href)
                            page_python_count += 1
                print(f"  Python вакансий на странице: {page_python_count}")
            except:
                pass

            if page < pages - 1:
                time.sleep(1)

        print(f"\nВсего найдено ссылок: {len(vacancy_links)}")
        print(f"Парсинг вакансий (нужно {target_count} с полными данными)...")
        print("-" * 60)

        complete_count = 0
        processed_count = 0

        for link in vacancy_links:
            if complete_count >= target_count:
                break

            processed_count += 1
            data = parse_vacancy_page(driver, link)

            if is_complete_vacancy(data):
                vacancies.append(data)
                complete_count += 1
                print(f"[{complete_count}/{target_count}] {data['Название вакансии'][:50]}")
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

        output_file = 'vacancies_moscow.xlsx'
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

        df.to_excel(writer, sheet_name='Вакансии', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Вакансии']

        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1
        })
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_fmt)

        worksheet.set_column('A:A', 45)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 15)
        worksheet.set_column('E:E', 30)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 22)
        worksheet.set_column('I:I', 22)
        worksheet.set_column('J:J', 22)
        worksheet.set_column('K:K', 40)
        worksheet.set_column('L:L', 15)

        salaries = df['Зарплата (avg, руб/мес)'].dropna()

        #ГРАФИК 1: СРЕДНЯЯ ЗАРАБОТНАЯ ПЛАТА
        print("Создание графика: Средняя зарплата...")

        if len(salaries) > 0:
            avg_salary = salaries.mean()
            median_salary = salaries.median()
            min_salary = salaries.min()
            max_salary = salaries.max()

            salary_stats_sheet = workbook.add_worksheet('Статистика по зарплате')
            fmt_title = workbook.add_format({'bold': True, 'font_size': 14})
            fmt = workbook.add_format({'font_size': 12})

            salary_stats_sheet.write('A1', 'СТАТИСТИКА ПО ЗАРАБОТНОЙ ПЛАТЕ', fmt_title)
            salary_stats_sheet.write('A2', '(все значения в рублях/месяц)', fmt)
            salary_stats_sheet.write('A4', f'Средняя зарплата:', fmt)
            salary_stats_sheet.write('B4', f'{avg_salary:,.0f} руб./мес.', fmt)
            salary_stats_sheet.write('A5', f'Медианная зарплата:', fmt)
            salary_stats_sheet.write('B5', f'{median_salary:,.0f} руб./мес.', fmt)
            salary_stats_sheet.write('A6', f'Минимальная:', fmt)
            salary_stats_sheet.write('B6', f'{min_salary:,.0f} руб./мес.', fmt)
            salary_stats_sheet.write('A7', f'Максимальная:', fmt)
            salary_stats_sheet.write('B7', f'{max_salary:,.0f} руб./мес.', fmt)
            salary_stats_sheet.write('A8', f'Вакансий с зарплатой:', fmt)
            salary_stats_sheet.write('B8', len(salaries), fmt)

            salary_stats_sheet.write('A10', 'Исходные валюты:', fmt_title)
            row = 11
            for curr, count in currency_counts.items():
                salary_stats_sheet.write(f'A{row}', f'  {curr}:', fmt)
                salary_stats_sheet.write(f'B{row}', count, fmt)
                row += 1

            salary_stats_sheet.write(f'A{row + 1}', 'Исходные периоды:', fmt_title)
            row += 2
            for period, count in period_counts.items():
                salary_stats_sheet.write(f'A{row}', f'  {period}:', fmt)
                salary_stats_sheet.write(f'B{row}', count, fmt)
                row += 1

            salary_stats_sheet.set_column('A:A', 40)
            salary_stats_sheet.set_column('B:B', 25)

            plt.figure(figsize=(10, 6))
            plt.hist(salaries, bins=10, color='#4472C4', edgecolor='black', alpha=0.7)
            plt.axvline(avg_salary, color='red', linestyle='--', linewidth=2, label=f'Средняя: {avg_salary:,.0f}')
            plt.axvline(median_salary, color='green', linestyle='--', linewidth=2,
                        label=f'Медиана: {median_salary:,.0f}')
            plt.title('Распределение зарплат Python-разработчиков в Москве (руб./мес.)')
            plt.xlabel('Зарплата (руб./мес.)')
            plt.ylabel('Количество вакансий')
            plt.legend()
            plt.tight_layout()

            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=150)
            img.seek(0)
            salary_stats_sheet.insert_image('D2', 'salary_dist.png', {'image_data': img})
            salary_stats_sheet.set_column('D:D', 60)
            salary_stats_sheet.set_row(1, 350)
            plt.close()

        #ГРАФИК 2: ОБЯЗАТЕЛЬНЫЕ НАВЫКИ
        print("Создание графика: Обязательные навыки...")

        all_skills = []
        for s in df['Ключевые навыки']:
            if pd.notna(s) and s:
                all_skills.extend([x.strip() for x in str(s).split(';')])

        if all_skills:
            top_skills = Counter(all_skills).most_common(15)
            skills_df = pd.DataFrame(top_skills, columns=['Навык', 'Количество'])

            skills_sheet = workbook.add_worksheet('Обязательные навыки')

            skills_sheet.write('A1', 'ТОП НАВЫКОВ PYTHON-РАЗРАБОТЧИКОВ', fmt_title)

            skills_sheet.write('A3', 'Навык', fmt_title)
            skills_sheet.write('B3', 'Количество вакансий', fmt_title)

            for idx, (skill, count) in enumerate(top_skills, 4):
                skills_sheet.write(f'A{idx}', skill, fmt)
                skills_sheet.write(f'B{idx}', count, fmt)

            skills_sheet.set_column('A:A', 35)
            skills_sheet.set_column('B:B', 25)

            plt.figure(figsize=(12, 8))
            bars = plt.barh(range(len(skills_df)), skills_df['Количество'][::-1], color='#70AD47', edgecolor='black')
            plt.yticks(range(len(skills_df)), skills_df['Навык'][::-1])
            plt.title('Обязательные навыки для Python-разработчиков (Топ-15)')
            plt.xlabel('Количество упоминаний в вакансиях')

            for bar, count in zip(bars, skills_df['Количество'][::-1]):
                plt.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                         str(count), ha='left', va='center', fontsize=9)

            plt.tight_layout()

            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=150)
            img.seek(0)
            skills_sheet.insert_image('D2', 'skills.png', {'image_data': img})
            skills_sheet.set_column('D:D', 70)
            skills_sheet.set_row(1, 500)
            plt.close()

        #ГРАФИК 3: ТРЕБОВАНИЯ К ОПЫТУ РАБОТЫ
        print("Создание графика: Опыт работы...")

        exp_counts = df['Опыт работы'].value_counts()
        if len(exp_counts) > 0:
            exp_sheet = workbook.add_worksheet('Требования к опыту')

            exp_sheet.write('A1', 'ТРЕБОВАНИЯ К ОПЫТУ РАБОТЫ', fmt_title)

            exp_sheet.write('A3', 'Опыт работы', fmt_title)
            exp_sheet.write('B3', 'Количество вакансий', fmt_title)
            exp_sheet.write('C3', 'Процент', fmt_title)

            for idx, (exp, count) in enumerate(exp_counts.items(), 4):
                pct = (count / len(df)) * 100
                exp_sheet.write(f'A{idx}', exp, fmt)
                exp_sheet.write(f'B{idx}', count, fmt)
                exp_sheet.write(f'C{idx}', f'{pct:.1f}%', fmt)

            exp_sheet.set_column('A:A', 30)
            exp_sheet.set_column('B:B', 25)
            exp_sheet.set_column('C:C', 15)

            plt.figure(figsize=(10, 6))
            bars = plt.bar(range(len(exp_counts)), exp_counts.values, color='#ED7D31', edgecolor='black')
            plt.xticks(range(len(exp_counts)), exp_counts.index, rotation=30, ha='right')
            plt.title('Требования к опыту работы Python-разработчиков')
            plt.xlabel('Опыт работы')
            plt.ylabel('Количество вакансий')

            for bar, count in zip(bars, exp_counts.values):
                plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                         str(count), ha='center', va='bottom', fontsize=9)

            plt.tight_layout()

            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=150)
            img.seek(0)
            exp_sheet.insert_image('D2', 'experience.png', {'image_data': img})
            exp_sheet.set_column('D:D', 60)
            exp_sheet.set_row(1, 350)
            plt.close()

        #ГРАФИК 4: ТИП ЗАНЯТОСТИ
        print("Создание графика: Тип занятости...")

        emp_counts = df['Занятость'].value_counts()
        if len(emp_counts) > 0:
            emp_sheet = workbook.add_worksheet('Тип занятости')

            emp_sheet.write('A1', 'ТИП ЗАНЯТОСТИ', fmt_title)

            emp_sheet.write('A3', 'Тип занятости', fmt_title)
            emp_sheet.write('B3', 'Количество', fmt_title)
            emp_sheet.write('C3', 'Процент', fmt_title)

            for idx, (emp, count) in enumerate(emp_counts.items(), 4):
                pct = (count / len(df)) * 100
                emp_sheet.write(f'A{idx}', emp, fmt)
                emp_sheet.write(f'B{idx}', count, fmt)
                emp_sheet.write(f'C{idx}', f'{pct:.1f}%', fmt)

            emp_sheet.set_column('A:A', 30)
            emp_sheet.set_column('B:B', 15)
            emp_sheet.set_column('C:C', 15)

            plt.figure(figsize=(8, 8))
            plt.pie(emp_counts.values, labels=emp_counts.index, autopct='%1.1f%%',
                    startangle=90, colors=['#4472C4', '#ED7D31', '#70AD47', '#FFC000', '#5B9BD5'])
            plt.title('Распределение по типу занятости')
            plt.tight_layout()

            img = io.BytesIO()
            plt.savefig(img, format='png', dpi=150)
            img.seek(0)
            emp_sheet.insert_image('D2', 'employment.png', {'image_data': img})
            emp_sheet.set_column('D:D', 50)
            emp_sheet.set_row(1, 400)
            plt.close()

        #ИТОГОВАЯ СТАТИСТИКА
        summary_sheet = workbook.add_worksheet('Описание результатов')

        summary_sheet.write('A1', 'ОПИСАНИЕ РЕЗУЛЬТАТОВ ПАРСИНГА', fmt_title)
        summary_sheet.write('A3', 'Общая информация:', fmt_title)
        summary_sheet.write('A4', f'Регион поиска: Москва', fmt)
        summary_sheet.write('A5', f'Всего проанализировано вакансий: {len(df)}', fmt)
        summary_sheet.write('A6', f'Все вакансии содержат ПОЛНЫЕ данные', fmt)
        summary_sheet.write('A7', f'Все зарплаты приведены к рублям/месяц', fmt)
        summary_sheet.write('A8', f'Курсы: 1 USD = {USD_TO_RUB} RUB, 1 EUR = {EUR_TO_RUB} RUB', fmt)

        if len(salaries) > 0:
            summary_sheet.write('A10', 'Средняя заработная плата (руб./мес.):', fmt_title)
            summary_sheet.write('A11', f'Средняя: {salaries.mean():,.0f} руб./мес.', fmt)
            summary_sheet.write('A12', f'Медианная: {salaries.median():,.0f} руб./мес.', fmt)
            summary_sheet.write('A13', f'Минимальная: {salaries.min():,.0f} руб./мес.', fmt)
            summary_sheet.write('A14', f'Максимальная: {salaries.max():,.0f} руб./мес.', fmt)

        summary_sheet.write('A16', 'Обязательные навыки:', fmt_title)
        if all_skills:
            top_5_skills = Counter(all_skills).most_common(5)
            for idx, (skill, count) in enumerate(top_5_skills, 17):
                summary_sheet.write(f'A{idx}', f'{idx - 16}. {skill} ({count} вакансий)', fmt)

        summary_sheet.write('A23', 'Требования к опыту:', fmt_title)
        if len(exp_counts) > 0:
            most_common_exp = exp_counts.idxmax()
            summary_sheet.write('A24', f'Наиболее востребован: {most_common_exp}', fmt)

        summary_sheet.write('A26', 'Распределение по исходным валютам:', fmt_title)
        row = 27
        for curr, count in currency_counts.items():
            summary_sheet.write(f'A{row}', f'  {curr}: {count} вакансий', fmt)
            row += 1

        summary_sheet.set_column('A:A', 60)

        writer.close()
        print(f"\nФайл сохранен: {output_file}")

    finally:
        driver.quit()


if __name__ == '__main__':
    main()