from aiogram import *
from aiogram.types import *

create_profile_kb = InlineKeyboardMarkup()
create_profile_btn = InlineKeyboardButton('Создать профиль', callback_data='create_profile')
create_profile_kb.add(create_profile_btn)

cancel_ikb = InlineKeyboardMarkup()
cancel_btn = InlineKeyboardButton('Отменить', callback_data='cancel')
cancel_ikb.add(cancel_btn)

tags_ikb = InlineKeyboardMarkup(row_width=1)
cats_btn = InlineKeyboardButton('Котята', callback_data='cats')
dogs_btn = InlineKeyboardButton('Собачки', callback_data='dogs')
birds_btn = InlineKeyboardButton('Птички', callback_data='birds')
hamster_btn = InlineKeyboardButton('Хомячки', callback_data='hamsters')
other_btn = InlineKeyboardButton('Другое', callback_data='others')
confirm_btn = InlineKeyboardButton('Подтвердить', callback_data='confirm')
tags_ikb.add(cats_btn, dogs_btn, birds_btn, hamster_btn, other_btn, confirm_btn, cancel_btn)

main_menu_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
show_profile_btn = KeyboardButton('Показать профиль')
change_profile_btn = KeyboardButton('Изменить профиль')
create_article_btn = KeyboardButton('Создать запись')
show_pics_btn = KeyboardButton('Показать смешную картиночку')
main_menu_kb.add(create_article_btn, show_pics_btn, show_profile_btn, change_profile_btn)