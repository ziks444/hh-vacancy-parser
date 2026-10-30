from datetime import datetime
import re
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

from transform import vacancy_id_from_url


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


def collect_vacancy_links(driver, query, area_id, pages, max_links, delay):
    #Сбор ссылок на все вакансии со страниц поиска
    vacancy_links = []

    for page in range(pages):
        url = f"https://hh.ru/search/vacancy?text={query.replace(' ', '+')}&area={area_id}&page={page}"
        print(f"Сбор ссылок: страница {page + 1}/{pages}...")

        driver.get(url)
        time.sleep(delay + 0.5)

        try:
            buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Понятно')]")
            if buttons:
                buttons[0].click()
                time.sleep(0.5)
        except:
            pass

        links = driver.find_elements(By.CSS_SELECTOR, "a[data-qa='serp-item__title']")
        page_count = 0
        for link in links:
            href = (link.get_attribute('href') or '').split('?')[0]
            if 'hh.ru/vacancy/' in href and href not in vacancy_links:
                vacancy_links.append(href)
                page_count += 1
        print(f"  Новых вакансий на странице: {page_count}")

        # Поиск закончился раньше, чем страницы
        if not links:
            break

        if len(vacancy_links) >= max_links:
            break

        time.sleep(delay)

    return vacancy_links[:max_links]


def _text(driver, selector):
    #Текст элемента или пустая строка, если элемента нет
    elements = driver.find_elements(By.CSS_SELECTOR, selector)
    return elements[0].text.strip() if elements else ''


def parse_vacancy_page(driver, url):
    #Парсинг одной страницы вакансии: сохраняем поля как есть, без обработки
    try:
        driver.get(url)
        time.sleep(1)

        salary_type = None
        if driver.find_elements(By.CSS_SELECTOR, "[data-qa='vacancy-salary-compensation-type-net']"):
            salary_type = 'net'
        elif driver.find_elements(By.CSS_SELECTOR, "[data-qa='vacancy-salary-compensation-type-gross']"):
            salary_type = 'gross'

        skills = []
        for skill_el in driver.find_elements(By.CSS_SELECTOR, "[data-qa='skills-element']"):
            skill_text = skill_el.text.strip()
            if skill_text:
                skills.append(skill_text)

        # Дата публикации есть только текстом: «Вакансия опубликована 23 октября 2026 в Москве»
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        published = re.search(r'Вакансия опубликована[^\n]*', body_text)

        return {
            'id': vacancy_id_from_url(url),
            'url': url,
            'title': _text(driver, "[data-qa='vacancy-title']"),
            'employer': _text(driver, "[data-qa='vacancy-company-name']"),
            'salary_text': _text(driver, "[data-qa='vacancy-salary']"),
            'salary_type': salary_type,
            'experience': _text(driver, "[data-qa='vacancy-experience']"),
            'employment': _text(driver, "[data-qa='common-employment-text']"),
            'schedule': _text(driver, "[data-qa='work-schedule-by-days-text']"),
            'working_hours': _text(driver, "[data-qa='working-hours-text']"),
            'work_format': _text(driver, "[data-qa='work-formats-text']"),
            'skills': skills,
            'address': _text(driver, "[data-qa='vacancy-view-raw-address']"),
            'published_text': published.group(0).strip() if published else '',
            'scraped_at': datetime.now().isoformat(timespec='seconds'),
        }
    except:
        return None
