import io
from collections import Counter

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from config import USD_TO_RUB, EUR_TO_RUB


def build_excel_report(df, currency_counts, period_counts, output_file):
    #Сохранение вакансий в Excel со статистикой и графиками
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')

    df.to_excel(writer, sheet_name='Вакансии', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Вакансии']

    fmt_title = workbook.add_format({'bold': True, 'font_size': 14})
    fmt = workbook.add_format({'font_size': 12})

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
