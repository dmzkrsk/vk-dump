# vk-dump

Скачивает инфу с вконтакта

Пока умеет только:

- альбомы
- картинки из избранного

Двухфакторная авторизация пока не поддерживаетсяы

Python 3.7+, asyncio

## Как запустить

1. [Создаем приложение ВК](https://vk.com/apps?act=manage)
2. `git clone https://github.com/dmzkrsk/vk-dump`
3. копируем `config.txt.sample` в `config.txt`
4. заполняем в нем `APP_ID` созданного приложения
5. Создаем виртуальное окружение (`virtualenv`) любимым способом
6. `pip install pipenv`
7. `pipenv install`
8. `python run.py <email> <password> albums`

Подробности в `run.py`
