# Сравниваем вакансии программистов

Учебный проект по нахождению средних зарплат для программистов
на основных 10 языках (из топа GitHub за последний год) в Москве
на сайтах [HH.ru](https://hh.ru/) и [SuperJob.ru](https://www.superjob.ru/)
___________________
### Требования
Нужен Python от версии 3.8.
Нужно 

### Как установить 
Скачайте код.
Нужно запустить `pip` (или `pip3` при наличии конфликтов с Python2) 
для установки зависимостей:
```commandline
pip install -r requirements.txt
```
Рекомендуется использовать [virtual/venv](https:..docs.python.org/3/library/venv.html) 
для изоляции проекта
______
### Переменные окружения
Определите переменную окружения в файле `.env` в формате: `ПЕРЕМЕННАЯ=значение`:
- `SJ_SECRET_KEY` — секретный ключ для работы с [API SuperJob](https://api.superjob.ru/info/)

### Работа со скриптом
Перед запуском нужно получить секретный ключ от SuperJob
и внести его в переменную окружения.

После запуска долго ждём (можно увидеть прогресс в логах),
после чего будут выведены две таблицы, со средними зарплатами по языкам, 
а также с количеством вакансий в целом и по скольки из них был совершён расчёт.
В случае с hh это 30 дней, а для SJ - за всё время (учитываются только активные вакансии)

```commandline
(venv) python3 vacs_in_hh_and_sj.py
```
Результат работы:
```commandline
+HeadHunter Moscow------+------------------+---------------------+------------------+
| Язык программирования | Вакансий найдено | Вакансий обработано | Средняя зарплата |
+-----------------------+------------------+---------------------+------------------+
| JavaScript            | 4784             | 1860                | 197520           |
| Python                | 3627             | 1740                | 215839           |
| Java                  | 3902             | 1780                | 272804           |
| TypeScript            | 1788             | 1720                | 224351           |
| C#                    | 2051             | 1720                | 209238           |
| PHP                   | 1905             | 1860                | 198854           |
| C++                   | 1883             | 1800                | 207534           |
| Shell                 | 278              | 1040                | 186855           |
| C                     | 4094             | 1680                | 193297           |
| Ruby                  | 302              | 1660                | 214096           |
+-----------------------+------------------+---------------------+------------------+
+SuperJob Moscow--------+------------------+---------------------+------------------+
| Язык программирования | Вакансий найдено | Вакансий обработано | Средняя зарплата |
+-----------------------+------------------+---------------------+------------------+
| JavaScript            | 94               | 72                  | 168002           |
| Python                | 63               | 40                  | 159535           |
| Java                  | 48               | 27                  | 189229           |
| TypeScript            | 31               | 26                  | 221892           |
| C#                    | 29               | 17                  | 172823           |
| PHP                   | 56               | 44                  | 161191           |
| C++                   | 48               | 34                  | 166691           |
| Shell                 | 6                | 5                   | 167500           |
| C                     | 41               | 30                  | 193033           |
| Ruby                  | 6                | 5                   | 143200           |
+-----------------------+------------------+---------------------+------------------+
```

### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).