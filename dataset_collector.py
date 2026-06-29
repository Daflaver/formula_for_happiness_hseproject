# -*- coding: utf-8 -*-
import vk_api
import time
import json
import os
import datetime
from tqdm import tqdm
import random

import os
from dotenv import load_dotenv 
load_dotenv() 
TOKEN = os.getenv("KATE_MOBILE_TOKEN")

TARGET_CITIES = {
    1: "Москва",
    2: "Санкт-Петербург",
    99: "Новосибирск",
    49: "Екатеринбург",
    60: "Казань",
    10: "Волгоград",
    153: "Хабаровск"
}

def get_target_users(users_per_city=25, existing_ids=None):
    """Ищем пользователей из разных городов России, исключая уже скачанных"""
    if existing_ids is None:
        existing_ids = set()

    all_open_users =[]

    for city_id, city_name in TARGET_CITIES.items():
        time.sleep(0.35)
        try:
            random_offset = random.randint(0, 800)

            users = vk.users.search(
                city=city_id,
                count=200,
                offset=random_offset, #сдвиг
                has_photo=1,
                fields="bdate,sex,city,counters",
                age_from=18,
                age_to=35
            )['items']

            #фильтр: открытые, не удаленные и те, кого нет в базе
            open_users =[
                u for u in users
                if not u.get('is_closed')
                and 'deactivated' not in u
                and str(u['id']) not in existing_ids #проверка на дубликаты
            ]

            all_open_users.extend(open_users[:users_per_city])

        except vk_api.exceptions.ApiError as e:
            print(f"Ошибка API при поиске в {city_name}: {e}")

    return all_open_users

vk_session = vk_api.VkApi(token=TOKEN)
vk = vk_session.get_api()

def calculate_age(bdate):
    """Считает возраст, если указан год рождения"""
    if not bdate or len(bdate.split('.')) != 3:
        return None
    try:
        birth_year = int(bdate.split('.')[2])
        return 2026 - birth_year
    except:
        return None

def parse_user(user):
    """Собираем профиль по формату ТЗ"""
    user_id = user['id']

    data = {
        "id": str(user_id),
        "city": user.get('city', {}).get('title', 'Unknown'),
        "age": calculate_age(user.get('bdate')),
        "gender": "female" if user.get('sex') == 1 else "male",
        "photos_num": user.get('counters', {}).get('photos', 0),
        "videos_num": user.get('counters', {}).get('videos', 0),
        "audio_num": user.get('counters', {}).get('audios', 0),
        "followers_num": user.get('counters', {}).get('followers', 0),
        "posts": {},
        "groups": {},
        "friends":[]
    }

    try:
        #Друзья
        time.sleep(0.35) # лимит ВК 3 запроса в секунду
        friends = vk.friends.get(user_id=user_id)['items']
        data['friends'] = friends
        data['friends_num'] = len(friends)

        #Группы
        time.sleep(0.35)
        groups = vk.groups.get(user_id=user_id, extended=1, fields="description")['items']
        data['groups_num'] = len(groups)
        for g in groups:
            data['groups'][str(g['id'])] = {
                "name": g.get('name', ''),
                "description": g.get('description', '')
            }

        #Посты
        time.sleep(0.35)
        wall = vk.wall.get(owner_id=user_id, count=100)['items']

        self_posts = 0
        reposts = 0

        for post in wall:
            post_id = str(post['id'])
            if 'copy_history' in post:
                reposts += 1
            else:
                self_posts += 1

            text = post.get('text', '')
            date = datetime.datetime.fromtimestamp(post['date']).strftime('%d.%m.%Y %H:%M:%S')

            if text.strip():
                data['posts'][post_id] = {
                    "text": text,
                    "date": date
                }

        data['self_posts_num'] = self_posts
        data['reposts_num'] = reposts

        #нет друзей/постов
        if data['friends_num'] == 0 or len(data['posts']) == 0:
            return None

        return data

    except vk_api.exceptions.ApiError:
        # Профиль закрыт от парсинга настройками приватности
        return None


##Запуск
if __name__ == "__main__":
    FILENAME = 'data.json'
    final_dataset =[]
    existing_ids = set()

    #читаем старый датасет(если он сущетсвует)
    if os.path.exists(FILENAME):
        try:
            with open(FILENAME, 'r', encoding='utf-8') as f:
                final_dataset = json.load(f)
            #запоминаем айди для ЧС
            for user in final_dataset:
                existing_ids.add(str(user['id']))
            print(f"Файл найден, в базе уже {len(final_dataset)} пользователей.")
        except json.JSONDecodeError:
            print("Файл data.json пуст.")
    else:
        print("Файл data.json не найден")


    target_users = get_target_users(users_per_city=30, existing_ids=existing_ids)

    added_count = 0
    for user in tqdm(target_users, desc="Сбор данных (стены, группы, друзья)"):
        user_data = parse_user(user)
        if user_data:
            final_dataset.append(user_data)
            added_count += 1

    with open(FILENAME, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)

    print(f"Добавлено {added_count} новых людей.")
    print(f"Теперь в базе {len(final_dataset)} пользователей.")

!pip install vk_api

"""#UPD
хотим добавлять новых пользователей в json. Проблемы: дубликаты, одмнаковая выдача вк. Поэтому добавим ЧС для айди, которые уже есть в нашей базе, и добавим сдвиг(offspring), для того, чтобы находить случайных людей каждый раз.
"""