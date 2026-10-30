from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

from transform import parse_salary, is_python_vacancy


def create_driver():
    #Настройка и запуск Chrome
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    return webdriver.Chrome(options=options)


def collect_vacancy_links(driver, query, pages):
    #Сбор ссылок на Python-вакансии со страниц поиска
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

    return vacancy_links


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
