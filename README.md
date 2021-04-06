[![Python](https://img.shields.io/badge/-Python-464646??style=flat-square&logo=Python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/-Django-464646??style=flat-square&logo=Django)](https://www.djangoproject.com/)
# Социальная сеть Yatube
Веб-приложение на Django. Социальная сеть с возможностью публикации фото 
с описанием, комментариями под постами, реализована система подписок. 
MVT-архитектура, пагинация и кэширование постов. 
Реализована верификация данных.
Приложение покрыто Unit-тестами.

## Установка:
1. Клонируйте репозиторий на локальную машину.
- ``git clone https://github.com/da-semenov/hw05_final``
2. Установите виртуальное окружение.
- ``python3 -m venv venv``
3. Активируйте виртуальное окружение.
- ``source venv/bin/activate``
4. Установите зависимости.
- ``pip install -r requirements.txt``
5. Выполните миграции.
- ``python manage.py migrate``
6. Запустите локальный сервер.
- ``python manage.py runserver``

## Основные использованные технологии
* [python 3.8](https://www.python.org/)
* [django](https://www.djangoproject.com/)

## Автор

* **Семенов Денис** - [da-semenov](https://github.com/da-semenov)
