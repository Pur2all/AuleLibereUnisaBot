import datetime
from shutil import Error
import UnisaFreeRooms
import os
import re
import redis
import telebot
import time
import threading


TOKEN_BOT = os.environ["TOKEN_BOT"]
ADMINS = os.environ["ADMINS"].split(";")


def get_redis_connection():

    return redis.from_url(os.environ["REDIS_URL"], decode_responses=True)


def make_buildings_keyboard_markup():
    markup = telebot.types.ReplyKeyboardMarkup()
    buttons = []

    for building in UnisaFreeRooms.buildings:
        temp_button = telebot.types.KeyboardButton(text=building)
        buttons.append(temp_button)

    markup.add(*buttons)

    return markup


def make_classroom_keyboard_markup(building):
    markup = telebot.types.ReplyKeyboardMarkup()
    buttons = []
    values = UnisaFreeRooms.rooms_for_buildings[UnisaFreeRooms.buildings[building]]

    for value in values:
        temp_button = telebot.types.KeyboardButton(text=value)
        buttons.append(temp_button)

    markup.add(*buttons)

    return markup


def set_user_prev_command(user_id, prev_command):
    users[user_id] = prev_command


def update_users_db():
    while True:
        time.sleep(60 * 60)
        redis_connection.hmset("users", users)
        print("Users db updated")


UnisaFreeRooms.setup()
bot = telebot.TeleBot(TOKEN_BOT)
selected_building_for_user = {}
redis_connection = get_redis_connection()
users = redis_connection.hgetall("users")


@bot.message_handler(commands=["start"])
def send_welcome(message):
    set_user_prev_command(message.from_user.id, "start")

    redis_connection.hmset("users", users)

    bot.send_message(message.chat.id,
    "Questo è un bot per cercare le aule libere ad Unisa, buona fortuna!\n\nInvia /help per avere una breve descrizione del bot")


@bot.message_handler(func=lambda message: "/admin_message" in message.text and str(message.from_user.id) in ADMINS)
def send_message_to_all_users(message):
    message = re.search(r"(?<=\/admin_message ).+", message.text).group()

    for user in users:
        try:
            bot.send_message(user, message)
        except Exception:
            del users[user]
        time.sleep(0.1)


@bot.message_handler(commands=["edifici", "aula", "now_edifici"])
def print_buildings_keyboard(message):
    markup = make_buildings_keyboard_markup()
    prev_command = None

    if datetime.date.today().weekday() < 5:
        prev_command = message.text.replace("/", "")

        bot.send_message(message.chat.id, "Scegli un edificio:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Oggi l'università è chiusa, studia a casa!")
    
    set_user_prev_command(message.from_user.id, prev_command)


@bot.message_handler(commands=["help"])
def print_help_message(message):
    set_user_prev_command(message.from_user.id, "None")

    help_message = "Questo bot ti permette di conoscere le aule libere in tutta l'Università degli Studi di Salerno \n" + \
        "Descrizione comandi: \n" + \
        "/help - Mostra questo messaggio \n" + \
        "/edifici - Mostra gli orari liberi delle aule nell'edificio scelto \n" + \
        "/aula - Mostra gli orari liberi di una precisa aula \n" + \
        "/now_edifici - Mostra le aule libere in un preciso edificio in questo esatto momento e fino a quando \n" + \
        "\n\n\n" + \
        "Per qualsiasi problema contattare @BondedByBlood \n" + \
        "Il codice di questo bot è pubblico, lo puoi trovare cliccando su questo link -> https://github.com/Pur2all/AuleLibereUnisaBot \n" + \
        "Sentiti libero di contribuire!"

    bot.send_message(message.chat.id, help_message)


@bot.message_handler(func=lambda message: users.get(message.from_user.id) == "aula" and message.text in UnisaFreeRooms.buildings)
def print_classrooms_keyboard(message):
    building = message.text
    selected_building_for_user[message.from_user.id] = building

    markup_classroom = make_classroom_keyboard_markup(building)

    bot.send_message(message.chat.id, "Scegli una classe:", reply_markup=markup_classroom)


@bot.message_handler(func=lambda message: users.get(message.from_user.id) == "edifici" and message.text in UnisaFreeRooms.buildings)
def print_free_hours_for_building(message):
    building = message.text
    free_times = UnisaFreeRooms.get_all_rooms_events_for_building(building)
    format_string = ""

    for room, free in free_times.items():
        if not free:
            format_string += room + " è occupata tutto il giorno\n"
        else:
            format_string += room + " è libera nei seguenti orari:\n"
            free = UnisaFreeRooms.format_time(free)
            for interval in free:
                format_string += "- Dalle " + interval[0] + " alle " + interval[1] + "\n"
        format_string += "\n\n"

    bot.send_message(message.chat.id, format_string, reply_markup=telebot.types.ReplyKeyboardRemove())

    set_user_prev_command(message.from_user.id, "None")


@bot.message_handler(func=lambda message: users.get(message.from_user.id) == "aula" and message.text in UnisaFreeRooms.rooms_for_buildings[UnisaFreeRooms.buildings[selected_building_for_user[message.from_user.id]]])
def print_free_hours_for_classroom(message):
    free_times = UnisaFreeRooms.format_time(UnisaFreeRooms.get_all_rooms_events_for_building(selected_building_for_user[message.from_user.id])[message.text])
    
    if not free_times:
        format_string = "L'aula è occupata tutto il giorno"
    else:
        format_string = "L'aula è libera nei seguenti orari:\n"

        for time in free_times:
            format_string += "- Dalle " + time[0] + " alle " + time[1] + "\n"

    bot.send_message(message.chat.id, format_string, reply_markup=telebot.types.ReplyKeyboardRemove())

    set_user_prev_command(message.from_user.id, "None")


@bot.message_handler(func=lambda message: users.get(message.from_user.id) == "now_edifici" and message.text in UnisaFreeRooms.buildings)
def print_free_hours_right_now(message):
    bot.send_message(message.chat.id, UnisaFreeRooms.get_all_free_rooms_right_now(message.text), reply_markup=telebot.types.ReplyKeyboardRemove())
    
    set_user_prev_command(message.from_user.id, "None")


update_db_thread = threading.Thread(target=update_users_db, daemon=True)
update_db_thread.start()

bot.polling(none_stop=False)
