import requests
import logging
from dotenv import load_dotenv
import os
from terminaltables import AsciiTable


def get_area_id_hh(name_area):
    """Функция получает id региона в hh по его названию, он может поменяться"""
    url_area = 'https://api.hh.ru/suggests/areas'
    params = {
        'text': name_area,
    }
    response = requests.get(url_area, params=params)
    response.raise_for_status()
    return response.json()['items'][0]['id']


def get_jobs_by_langs_hh(prof_name, area_name, period_job, languages):
    """Нахождение вакансий в hh по всем языкам"""
    url_job = 'https://api.hh.ru/vacancies'
    lang_jobs = {}
    for lang in languages:
        params = {
            'text': f'{prof_name} {lang}',
            'area': get_area_id_hh(area_name),
            'period': period_job,
            'per_page': 100,
        }
        response = requests.get(url_job, params=params)
        response.raise_for_status()
        lang_jobs[lang] = response.json()['found']
    return lang_jobs


def get_jobs_by_lang_with_salary_hh(prof_name, area_name, period_job, lang):
    """Функция получает все вакансии по определённому языку с пагинацией"""
    url_job = 'https://api.hh.ru/vacancies'
    per_page = 100
    items = []
    for page in range(2000//per_page):
        logging.info(f'Язык {lang}, страница {page}')
        params = {
            'text': f'{prof_name} {lang}',
            'area': get_area_id_hh(area_name),
            'period': period_job,
            'per_page': per_page,
            'only_with_salary': True,
        }
        response = requests.get(url_job, params=params)
        response.raise_for_status()
        items.extend(response.json()['items'])
    return items


def predict_rub_salary_hh(vacancy):
    """
    Возвращает либо зп, либо None.
    Если есть от и до, то выводит среднее.
    Если есть только от, то умножаем на 1,2
    Если есть только до, то умножаем на 0,8
    """
    salary = vacancy['salary']
    if salary:
        if salary['currency'] == 'RUR':
            if salary['to']:
                if salary['from']:
                    return (salary['to'] + salary['from']) * 0.5
                else:
                    return salary['to'] * 0.8
            else:
                if salary['from']:
                    return salary['from'] * 1.2
    return None


def predict_rub_salary_url_hh(id_job):
    """возвращение ЗП по определённой вакансии"""
    url_job = 'https://api.hh.ru/vacancies'
    url = f'{url_job}/{id_job}'
    response = requests.get(url)
    response.raise_for_status()

    return predict_rub_salary_hh(response.json())


def get_average_salary_by_langs_hh(prof_name, area_name, period_job, langs):
    """Функция расчёта средних зарплат по списку языков из hh"""
    jobs_langs = get_jobs_by_langs_hh(prof_name, area_name, period_job, langs)
    info_by_langs = {}
    for lang in langs:
        logging.info(lang)
        info_by_langs[lang] = {}
        info_by_langs[lang]["vacancies_found"] = jobs_langs[lang]
        items = get_jobs_by_lang_with_salary_hh(prof_name, area_name, period_job, lang)
        vacancies_processed, sum_salary = 0, 0
        len_items = len(items)
        for item in items:
            salary_item = predict_rub_salary_hh(item)
            if salary_item:
                vacancies_processed += 1
                sum_salary += salary_item
                logging.info(f' {vacancies_processed} из {len_items}. {int(100*vacancies_processed/len_items)}')

        info_by_langs[lang]['vacancies_processed'] = vacancies_processed
        if vacancies_processed:
            info_by_langs[lang]['average_salary'] = int(sum_salary/vacancies_processed)
        else:
            info_by_langs[lang]['average_salary'] = 0
        logging.info(info_by_langs[lang])
    return info_by_langs


def get_id_category_by_title_sj(title_category, headers):
    """Поиск кода искомой категории в списке категорий"""
    def find_title(item, keys, title_category):
        if item.get('positions'):
            for item2 in item['positions']:
                find_title(item2, keys, title_category)
        if item['title'].find(title_category) >= 0:
            keys.append(item['key'])

    url_cat = 'https://api.superjob.ru/2.0/catalogues/'
    response = requests.get(url_cat, headers=headers)
    response.raise_for_status()
    keys = []
    for item in response.json():
        find_title(item, keys, title_category)
    return keys


def predict_rub_salary_for_sj(vacancy):
    """
    Возвращает либо зп, либо None.
    Если есть от и до, то выводит среднее.
    Если есть только от, то умножаем на 1,2
    Если есть только до, то умножаем на 0,8
    """
    if vacancy['currency'] == 'rub':
        if int(vacancy['payment_to']) > 0:
            if int(vacancy['payment_from']) > 0:
                return (int(vacancy['payment_to']) + int(vacancy['payment_from']))*0.5
            else:
                return int(vacancy['payment_to']) * 0.8
        elif int(vacancy['payment_from']) > 0:
            return int(vacancy['payment_from']) * 1.2
    return None


def get_jobs_from_pages_sj(params, headers, period_job):
    """Получение всех записей с заданными параметрами из sj"""
    url_api = 'https://api.superjob.ru/2.0/vacancies/'
    params['count'] = 100
    page = 0
    params['page'] = page
    if period_job > 7:
        params['period'] = 0
        logging.info(f'Для SJ считаем за всё время так как {period_job} больше 7')
    elif period_job >= 5:
        params['period'] = 7
        logging.info(f'Для SJ считаем за неделю, так как {period_job} ближе к 7')
    elif period_job > 2:
        params['period'] = 3
        logging.info(f'Для SJ считаем за три дня, так как {period_job} ближе к 3')
    else:
        params['period'] = 1
        logging.info(f'Для SJ считаем за день, так как {period_job} ближе к 1')
    response = requests.get(url_api, headers=headers, params=params)
    response.raise_for_status()
    items_on_page = response.json()
    items_all = items_on_page['objects']
    while items_on_page['more']:
        page += 1
        params['page'] = page
        response = requests.get(url_api, headers=headers, params=params)
        response.raise_for_status()
        items_on_page = response.json()
        items_all.extend(items_on_page['objects'])
    return items_all


def get_jobs_by_lang_with_salary_sj(params, headers, lang, period_job):
    """Получение зарплаты по языку в sj(поиск по всему тексту вакансии)"""
    params['keyword'] = lang
    items_lang = get_jobs_from_pages_sj(params, headers, period_job)
    vacancies_processed = 0
    sum_salary = 0
    for item in items_lang:
        salary = predict_rub_salary_for_sj(item)
        if salary:
            vacancies_processed += 1
            sum_salary += salary
    if vacancies_processed > 0:
        average_salary = int(sum_salary/vacancies_processed)
    else:
        average_salary = None
    lang_settings = {
        'vacancies_found': len(items_lang),
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }
    return lang_settings


def get_jobs_by_lang_with_salary_in_table(languages, langs_settings, name_table):
    """Печать в консоль сводной таблицы по зарплатам по языкам"""
    table_headers = ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']

    table_data = [table_headers, ]
    for lang in languages:
        table_row = [
            lang,
            langs_settings[lang]['vacancies_found'],
            langs_settings[lang]['vacancies_processed'],
            langs_settings[lang]['average_salary']
        ]
        table_data.append(table_row)
    table_instance = AsciiTable(table_data, name_table)
    print(table_instance.table)


def get_average_salary_by_lang_sj(category_sj, area_name, period_job, langs, headers):
    """Функция расчёта средних зарплат по списку языков из sj"""
    id_category = get_id_category_by_title_sj(category_sj, headers)
    logging.info(f'{id_category} - список key категории {category_sj}')
    params = {
        'town': area_name,
        'catalogues': id_category[0]
    }

    langs_settings = {}
    for lang in langs:
        langs_settings[lang] = get_jobs_by_lang_with_salary_sj(
            params,
            headers,
            lang,
            period_job
        )
    return langs_settings


if __name__ == '__main__':
    load_dotenv()
    sj_secret_key = os.getenv('SJ_SECRET_KEY')
    area_name = 'Москва'
    period_job = 30
    logging.basicConfig(level=logging.INFO)
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s"
    )

    prof_name = 'программист'
    languages = [
        'JavaScript',
        'Python',
        'Java',
        'TypeScript',
        'C#',
        'PHP',
        'C++',
        'Shell',
        'C',
        'Ruby'
    ]
    headers_sj = {
        'X-Api-App-Id': sj_secret_key
    }
    category_sj = 'Разработка, программирование'

    langs_hh_salary = get_average_salary_by_langs_hh(
        prof_name,
        area_name,
        period_job,
        languages
    )

    get_jobs_by_lang_with_salary_in_table(
        languages,
        langs_hh_salary,
        'HeadHunter Moscow'
    )

    get_jobs_by_lang_with_salary_in_table(
        languages,
        get_average_salary_by_lang_sj(
            category_sj,
            area_name,
            period_job,
            languages,
            headers_sj
        ),
        'SuperJob Moscow'
    )

