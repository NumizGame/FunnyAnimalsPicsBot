from aiogram import *
import sqlite3 as sq
from config import token
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from keyboards import *
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from photo_tags_determinant import determine_photo_tags
import asyncio
import os
from random import choice

storage = MemoryStorage()
bot = Bot(token)
disp = Dispatcher(bot, storage=storage)

class CreateProfileStates(StatesGroup):
    start_creating = State()
    set_name = State()
    set_picture = State()
    set_desc = State()
    set_tags = State()

class CreateArticleStates(StatesGroup):
    set_article_photo = State()
    set_article_caption = State()

async def on_startup(_):
    with sq.connect('funny_animals_bot.db') as db:
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS animals_pictures ('
                       'link TEXT NOT NULL PRIMARY KEY, '
                       'caption TEXT, '
                       'picture_tag VARCHAR(40) NOT NULL,'
                       'likes INT,'
                       'author VARCHAR(80) NOT NULL)')

        cursor.execute('CREATE TABLE IF NOT EXISTS users ('
                       'user_id TEXT NOT NULL PRIMARY KEY,'
                       'name TEXT NOT NULL,'
                       'photo TEXT,'
                       'description TEXT,'
                       'selected_tags TEXT)')


        db.commit()

#проверка на наличие пользователя в базе данных
def is_registered(user_id):
    with sq.connect('funny_animals_bot.db') as db:
        cursor = db.cursor()
        current_user = cursor.execute(f'SELECT name FROM users WHERE user_id = "{user_id}"').fetchall()
        db.commit()

        if current_user:
            return True

        else:
            return False


#ЛОГГИРОВАНИЕ

@disp.message_handler(commands=['start'], state=None)
async def send_start(message):
    if not is_registered(message.from_user.id):
        await bot.send_message(message.chat.id, '<b>Привет, я FunnyAnimalsBot! Сейчас ты можешь создать свой профиль, чтобы смотреть смешные картиночки с животными и самому их добавлять!!!</b>', parse_mode='HTML', reply_markup=create_profile_kb)

        await CreateProfileStates.start_creating.set()

    else:
        await bot.send_message(message.chat.id, '<b>Добро пожаловать вновь! </b>', parse_mode='HTML', reply_markup=main_menu_kb)

    await message.delete()

@disp.callback_query_handler(text='cancel', state='*')
async def cancel(callback, state):
    await callback.answer('Действие отменено')
    await callback.message.delete()

    await state.finish()

@disp.callback_query_handler(text='create_profile', state=CreateProfileStates.start_creating)
async def name_handler(callback, state):
    async with state.proxy() as data_storage:
        data_storage['reg_mes'] = callback.message

    await callback.message.edit_text('<b>Окей, пришли мне свой никнейм</b>', parse_mode='HTML', reply_markup=cancel_ikb)

    await CreateProfileStates.next()

@disp.message_handler(state=CreateProfileStates.set_name)
async def setting_name(message, state):
    async with state.proxy() as data_storage:
        data_storage['id'] = message.from_user.id
        data_storage['name'] = message.text

        reg_message = data_storage['reg_mes']

    await message.delete()
    await reg_message.edit_text('<b>Теперь пришли фото твоего профиля!</b>', parse_mode='HTML', reply_markup=cancel_ikb)

    await CreateProfileStates.next()

@disp.message_handler(content_types=['photo'], state=CreateProfileStates.set_picture)
async def setting_picture(message, state):
    async with state.proxy() as data_storage:
        data_storage['photo'] = message.photo[0].file_id

        reg_message = data_storage['reg_mes']

    await message.delete()
    await reg_message.edit_text('<b>Отлично, теперь жду описание твоего профиля(необязательно)</b>', parse_mode='HTML', reply_markup=cancel_ikb)

    await CreateProfileStates.next()

@disp.message_handler(state=CreateProfileStates.set_desc)
async def setting_desc(message, state):
    async with state.proxy() as data_storage:
        data_storage['desc'] = message.text
        data_storage['tags'] = []

        reg_message = data_storage['reg_mes']

    await message.delete()
    await reg_message.edit_text('<b>И наконец, выбери те категории животных, которые тебе нравятся!</b>', parse_mode='HTML', reply_markup=tags_ikb)

    await CreateProfileStates.next()

@disp.callback_query_handler(lambda callback_query: callback_query.data in ['cats', 'dogs', 'birds', 'hamsters', 'others'], state=CreateProfileStates.set_tags)
async def setting_tags(callback, state):
    await callback.answer('Добавлено')

    async with state.proxy() as data_storage:
        users_tags = data_storage['tags']

        if callback.data not in users_tags:
            users_tags.append(callback.data)


@disp.callback_query_handler(text='confirm', state=CreateProfileStates.set_tags)
async def confirm_registration(callback, state):
    try:
        await callback.answer('Подтверждаю')

        async with state.proxy() as data_storage:
            reg_message = data_storage['reg_mes']

            with sq.connect('funny_animals_bot.db') as db:
                cursor = db.cursor()

                if not is_registered(callback.from_user.id):
                    cursor.execute(f'''INSERT INTO users VALUES ("{data_storage['id']}", "{data_storage['name']}", "{data_storage['photo']}", "{data_storage['desc']}", "{data_storage['tags']}")''')
                    await bot.send_message(callback.message.chat.id, '<b>Отлично, твой профиль создан! Теперь ты можешь использовать весь мой функционал!</b>', parse_mode='HTML', reply_markup=main_menu_kb)

                else:
                    cursor.execute(f'''UPDATE users SET name = "{data_storage['name']}", photo = "{data_storage['photo']}", description = "{data_storage['desc']}", selected_tags = "{data_storage['tags']}" WHERE user_id = "{data_storage['id']}"''')
                    await bot.send_message(callback.message.chat.id, '<b>Твой профиль был успешно обновлен !</b>', parse_mode='HTML', reply_markup=main_menu_kb)

                db.commit()

    except Exception:
        await reg_message.edit_text('<b>Упссс, что-то пошло не так, попробуй создать профиль сначала или обратись в службу поддержки https://t.me/ThisIsMyShadow  :(</b>', parse_mode='HTML')

    finally:
        await reg_message.delete()

        await state.finish()


#ВЫВОД ИНФОРМАЦИИ О ПРОФИЛЕ

@disp.message_handler(lambda message: is_registered(message.from_user.id), text='Показать профиль', state=None)
async def show_profile(message):
    with sq.connect('funny_animals_bot.db') as db:
        cursor = db.cursor()
        current_user = cursor.execute(f'SELECT name, photo, description, selected_tags FROM users WHERE user_id = "{message.from_user.id}"').fetchall()[0]
        db.commit()

    chosen_tags = current_user[3][1:-1].replace("'", "")    #форматируем строку для вывода

    await bot.send_photo(message.chat.id, current_user[1], caption=f'<b>{current_user[0]}\n{current_user[2]}\nЛюбимые категории: {chosen_tags}</b>', parse_mode='HTML')
    await message.delete()


#ИЗМЕНЕНИЕ ПРОФИЛЯ

@disp.message_handler(lambda message: is_registered(message.from_user.id), text='Изменить профиль', state=None)
async def change_profile(message, state):
    async with state.proxy() as data_storage:
        data_storage['reg_mes'] = await bot.send_message(message.chat.id, '<b>Для начала пришли мне новый никнейм(если ты не хочешь что-либо менять, просто отправь тот же самый текст/фото</b>', parse_mode='HTML', reply_markup=cancel_ikb)

    await message.delete()

    await CreateProfileStates.set_name.set()


#ДОБАВЛЕНИЕ ФОТОГРАФИЙ

@disp.message_handler(lambda message: is_registered(message.from_user.id), text='Создать запись', state=None)
async def start_creating_article(message, state):
    async with state.proxy() as data_storage:
        data_storage['article_mes'] = await bot.send_message(message.chat.id, '<b>Приветствую тебя в режиме создания статьи. Для начала отправь мне смешное фото животного.</b>', parse_mode='HTML', reply_markup=cancel_ikb)

    await message.delete()

    await CreateArticleStates.set_article_photo.set()


@disp.message_handler(content_types=['photo'], state=CreateArticleStates.set_article_photo)
async def setting_article_photo(message, state):
    async with state.proxy() as data_storage:
        create_article_mes = data_storage['article_mes']

        data_storage['photo'] = message.photo[0].file_id

        file_info = await bot.get_file(message.photo[0].file_id)
        file_ext = file_info.file_path.split('.')[-1]
        article_photo_path = f'users_photos/{message.photo[0].file_unique_id}.{file_ext}'

        data_storage['photo_path'] = article_photo_path


    await message.photo[-1].download(article_photo_path)

    await create_article_mes.edit_text('<b>Отлично, теперь пришли мне описание твоего фото!</b>', parse_mode='HTML', reply_markup=cancel_ikb)
    await message.delete()

    await CreateArticleStates.next()


@disp.message_handler(state=CreateArticleStates.set_article_caption)
async def setting_article_caption(message, state):
    try:
        async with state.proxy() as data_storage:
            article_photo = data_storage['photo']
            article_photo_path = data_storage['photo_path']
            create_article_mes = data_storage['article_mes']

        article_caption = message.text
        article_picture_tags = determine_photo_tags(article_photo_path)
        article_likes = 0

        os.remove(article_photo_path)

        with sq.connect('funny_animals_bot.db') as db:
            cursor = db.cursor()
            article_author = cursor.execute(f'SELECT name FROM users WHERE user_id = "{message.from_user.id}"').fetchall()[0][0]

            if article_picture_tags != []:
                cursor.execute(f'INSERT INTO animals_pictures VALUES ("{article_photo}", "{article_caption}", "{article_picture_tags}", {article_likes}, "{article_author}")')
                await create_article_mes.edit_text('<b>Отлично, твоя статья была добавлена! Теперь ты можешь увидеть ее и много других смешных статей в разделе "Показать смешную картиночку"</b>', parse_mode='HTML')

            else:
                await create_article_mes.edit_text('<b>Извини, но я не узнал на твоей картинке какое-либо животное. К сожалению я еще учусь распознавать объекты, поэтому попробуй загрузить другую картинку ! </b>', parse_mode='HTML')

            db.commit()

    except Exception:
        await create_article_mes.edit_text('<b>Упссс, что-то пошло не так, попробуй создать статью сначала или обратись в службу поддержки https://t.me/ThisIsMyShadow  :(</b>', parse_mode='HTML')

    finally:
        await message.delete()
        await state.finish()

        await asyncio.sleep(3)
        await create_article_mes.delete()


#ПОКАЗ КАРТИНОК

@disp.message_handler(lambda message: is_registered(message.from_user.id), text='Показать смешную картиночку', state=None)
async def show_picture(message, state):
    with sq.connect('funny_animals_bot.db') as db:
        cursor = db.cursor()
        chosen_tags = cursor.execute(f'SELECT selected_tags FROM users WHERE user_id = "{message.from_user.id}"').fetchall()[0][0][1:-1].replace("'", '').split(', ')
        random_tag = choice(chosen_tags)

        relevant_articles = cursor.execute(f'SELECT link, caption, likes, author FROM animals_pictures WHERE picture_tag LIKE "%{random_tag}%"').fetchall()

        random_article = choice(relevant_articles)

        db.commit()

    current_photo_likes = random_article[2]
    picture_link = random_article[0]

    picture_caption = f'<b>{random_article[1]}\n\nАвтор: {random_article[3]}</b>'

    like_ikb = InlineKeyboardMarkup()
    like_btn = InlineKeyboardButton(f'{current_photo_likes} ❤️', callback_data='like')
    like_ikb.add(like_btn)

    article = await bot.send_photo(message.chat.id, random_article[0], caption=picture_caption, parse_mode='HTML', reply_markup=like_ikb)

    async with state.proxy() as data_storage:
        data_storage['article'] = article
        data_storage['picture_link'] = picture_link
        data_storage['likes'] = current_photo_likes
        data_storage['picture_caption'] = picture_caption


    await message.delete()


@disp.callback_query_handler(text='like', state='*')
async def like_picture_event(callback, state):
    async with state.proxy() as data_storage:
        current_photo_likes = data_storage['likes']
        article = data_storage['article']
        picture_caption = data_storage['picture_caption']
        picture_link = data_storage['picture_link']

        data_storage['likes'] += 1

    with sq.connect('funny_animals_bot.db') as db:
        cursor = db.cursor()

        cursor.execute(f'UPDATE animals_pictures SET likes = likes + 1 WHERE link = "{picture_link}"')

        db.commit()

    like_ikb = InlineKeyboardMarkup()
    like_btn = InlineKeyboardButton(f'{current_photo_likes} ❤️', callback_data='like')
    like_ikb.add(like_btn)

    await callback.answer('🥰🥰🥰')

    await article.edit_caption(caption=picture_caption, parse_mode='HTML', reply_markup=like_ikb)

if __name__ == '__main__':
    executor.start_polling(disp, skip_updates=True, on_startup=on_startup)