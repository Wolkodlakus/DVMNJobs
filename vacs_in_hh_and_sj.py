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


def get_dif_all_and_period_hh(url_vac, prof_name, area_name, period_vac):
    """Вычисление количества вакансий в регионе всего и за определённый период"""
    params = {
        'text': prof_name,
        'area': get_area_id_hh(area_name),
        'per_page': 100,
    }
    response = requests.get(url_vac, params=params)
    response.raise_for_status()
    numb_all = response.json()['found']
    params['period'] = period_vac
    response = requests.get(url_vac, params=params)
    response.raise_for_status()
    numb_period = response.json()['found']
    logging.info(f'Всего вакансий в регионе {area_name} - {numb_all}, а за период {period_vac} - {numb_period}')
    logging.info(f'Разница {numb_all - numb_period}')


def get_vacs_by_langs_hh(url_vac, prof_name, area_name, period_vac, languages):
    """Нахождение вакансий в hh по всем языкам"""
    lang_vacs = {}
    for lang in languages:
        params = {
            'text': f'{prof_name} {lang}',
            'area': get_area_id_hh(area_name),
            'period': period_vac,
            'per_page': 100,
        }
        response = requests.get(url_vac, params=params)
        response.raise_for_status()
        lang_vacs[lang] = response.json()['found']
    return lang_vacs


def get_vacs_by_lang_with_salary_hh(url_vac, prof_name, area_name, period_vac, lang):
    """Функция получает все вакансии по определённому языку с пагинацией"""
    per_page = 100
    items = []
    for page in range(2000//per_page):
        logging.info(f'Язык {lang}, страница {page}')
        params = {
            'text': f'{prof_name} {lang}',
            'area': get_area_id_hh(area_name),
            'period': period_vac,
            'per_page': per_page,
            'only_with_salary': True,
        }
        response = requests.get(url_vac, params=params)
        response.raise_for_status()
        items.extend(response.json()['items'])
    return items


def predict_rub_salary_hh(vac):
    """
    Возвращает либо зп, либо None.
    Если есть от и до, то выводит среднее.
    Если есть только от, то умножаем на 1,2
    Если есть только до, то умножаем на 0,8
    """
    salary = vac['salary']
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


def predict_rub_salary_url_hh(url_vac, id_vac):
    """возвращение ЗП по определённой вакансии"""
    url = f'{url_vac}/{id_vac}'
    response = requests.get(url)
    response.raise_for_status()

    return predict_rub_salary_hh(response.json())


def average_salary_by_langs_hh(url_vac, prof_name, area_name, period_vac, langs):
    """Функция расчёта средних зарплат по списку языков из hh"""
    vacs_langs = get_vacs_by_langs_hh(url_vac, prof_name, area_name, period_vac, langs)
    info_by_langs = {}
    for lang in langs:
        logging.info(lang)
        info_by_langs[lang] = {}
        info_by_langs[lang]["vacancies_found"] = vacs_langs[lang]
        items = get_vacs_by_lang_with_salary_hh(url_vac, prof_name, area_name, period_vac, lang)
        vacancies_processed, sum_salary = 0, 0
        # sum_salary_item = [] # Закомментирован второй вариант
        len_items = len(items)
        for item in items:
            salary_item = predict_rub_salary_hh(item)
            # sum_salary_item.append(salary_item)
            if salary_item:
                vacancies_processed += 1
                sum_salary += salary_item
                logging.info(f' {vacancies_processed} из {len_items}. {int(100*vacancies_processed/len_items)}')
        # vacancies_processed_ = sum(1 for _ in filter(None.__ne__, sum_salary_item))
        # sum_salary_ = sum([x for x in sum_salary_item if x])

        info_by_langs[lang]['vacancies_processed'] = vacancies_processed
        if vacancies_processed:
            info_by_langs[lang]['average_salary'] = int(sum_salary/vacancies_processed)
        else:
            info_by_langs[lang]['average_salary'] = 0
        logging.info(info_by_langs[lang])
    return info_by_langs


def get_id_cat_by_title_sj(title_categ, headers):
    """Поиск кода искомой категории в списке категорий"""
    def find_title(item, keys, title_categ):
        if item.get('positions'):
            for item2 in item['positions']:
                find_title(item2, keys, title_categ)
        if item['title'].find(title_categ) >= 0:
            keys.append(item['key'])

    url_cat = 'https://api.superjob.ru/2.0/catalogues/'
    response = requests.get(url_cat, headers=headers)
    response.raise_for_status()
    keys = []
    for item in response.json():
        find_title(item, keys, title_categ)
    return keys


def predict_rub_salary_for_sj(vac):
    """
    Возвращает либо зп, либо None.
    Если есть от и до, то выводит среднее.
    Если есть только от, то умножаем на 1,2
    Если есть только до, то умножаем на 0,8
    """
    if vac['currency'] == 'rub':
        if int(vac['payment_to']) > 0:
            if int(vac['payment_from']) > 0:
                return (int(vac['payment_to']) + int(vac['payment_from']))*0.5
            else:
                return int(vac['payment_to']) * 0.8
        elif int(vac['payment_from']) > 0:
            return int(vac['payment_from']) * 1.2
    return None


def get_vacs_from_pages_sj(url_api, params, headers, period_vac):
    """Получение всех записей с заданными параметрами из sj"""
    params['count'] = 100
    page = 0
    params['page'] = page
    if period_vac > 7:
        params['period'] = 0
        logging.info(f'Для SJ считаем за всё время так как {period_vac} больше 7')
    elif period_vac >= 5:
        params['period'] = 7
        logging.info(f'Для SJ считаем за неделю, так как {period_vac} ближе к 7')
    elif period_vac > 2:
        params['period'] = 3
        logging.info(f'Для SJ считаем за три дня, так как {period_vac} ближе к 3')
    else:
        params['period'] = 1
        logging.info(f'Для SJ считаем за день, так как {period_vac} ближе к 1')
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


def get_vacs_by_lang_with_salary_sj(url_api, params, headers, lang, period_vac):
    """Получение зарплаты по языку в sj(поиск по всему тексту вакансии)"""
    params['keyword'] = lang
    items_lang = get_vacs_from_pages_sj(url_api, params, headers, period_vac)
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


def get_vacs_by_lang_with_salary_in_table(languages, langs_settings, name_table):
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


def average_salary_by_lang_sj(url_api, category_sj, area_name, period_vac, langs, headers):
    """Функция расчёта средних зарплат по списку языков из sj"""
    id_cat = get_id_cat_by_title_sj(category_sj, headers)
    logging.info(f'{id_cat} - список key категории {category_sj}')
    params = {
        'town': area_name,
        'catalogues': id_cat[0]
    }

    langs_settings = {}
    for lang in langs:
        langs_settings[lang] = get_vacs_by_lang_with_salary_sj(url_api, params, headers, lang, period_vac)
    return langs_settings


if __name__ == '__main__':
    load_dotenv()
    sj_secret_key = os.getenv('SJ_SECRET_KEY')
    area_name = 'Москва'
    period_vac = 30
    logging.basicConfig(level=logging.INFO)
    logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s")

    url_vac_hh = 'https://api.hh.ru/vacancies'
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
    url_api_sj = 'https://api.superjob.ru/2.0/vacancies/'
    headers_sj = {
        'X-Api-App-Id': sj_secret_key
    }
    category_sj = 'Разработка, программирование'

    langs_hh_salary = average_salary_by_langs_hh(url_vac_hh, prof_name, area_name, period_vac, languages)

    get_vacs_by_lang_with_salary_in_table(
        languages,
        langs_hh_salary,
        'HeadHunter Moscow'
    )

    get_vacs_by_lang_with_salary_in_table(
        languages,
        average_salary_by_lang_sj(url_api_sj, category_sj, area_name, period_vac, languages, headers_sj),
        'SuperJob Moscow'
    )

