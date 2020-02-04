import telebot
import FreeRoom
import datetime
import os 
import redis
import re
import time

TOKEN = "783944951:AAHdmcNjyI-8fZsSKv_-hIMp5MLeBkbDUvc"


def get_redis_info():
    redis_url = os.environ["REDIS_URL"]

    url_splitted = re.findall(r"([^:\/@]+)", redis_url)

    redis_user = url_splitted[1]
    redis_password = url_splitted[2]
    redis_host = url_splitted[3]
    redis_port = url_splitted[4]

    return redis_host, redis_port, redis_user, redis_password


def make_buildings_keyboard_markup():
    markup = telebot.types.ReplyKeyboardMarkup()
    buttons = []

    for key in FreeRoom.buildings:
        temp_button = telebot.types.KeyboardButton(text=key)
        buttons.append(temp_button)
    markup.add(*buttons)

    return markup


def make_classroom_keyboard_markup(building):
    markup = telebot.types.ReplyKeyboardMarkup()
    buttons = []
    values = FreeRoom.rooms_for_buildings[FreeRoom.buildings[building]]

    for value in values:
        temp_button = telebot.types.KeyboardButton(value)
        buttons.append(temp_button)
    markup.add(*buttons)

    return markup


FreeRoom.setup()
bot = telebot.TeleBot(TOKEN)
building : str = None
prev_command : dict = {}
redis_info = get_redis_info()
redis_connection = redis.Redis(redis_info[0], redis_info[1], client_name=redis_info[2], password=redis_info[3], decode_responses=True)
admins = os.environ["ADMINS"].split(";")
users = redis_connection.hgetall("users")


@bot.message_handler(commands=["start"])
def send_welcome(message):
    users[message.from_user.id] = "start"
    redis_connection.hmset("users", users)

    bot.send_message(message.chat.id, "Questo è un bot per cercare le aule libere ad Unisa, buona fortuna!")


@bot.message_handler(func=lambda message: "/admin_message" in message.text and message.from_user.id in admins)
def send_message_to_all_users(message):
    message = re.search(r"(?<=\/admin_message ).+", message.text).group()
    for user in users:
        bot.send_message(user, message)


@bot.message_handler(commands=["edifici", "aula"])
def print_buildings_keyboard(message):
    markup = make_buildings_keyboard_markup()
    prev_command = None

    if datetime.date.today().weekday() < 5:
        prev_command = message.text.replace("/", "")

        bot.send_message(message.chat.id, "Scegli un edificio:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Oggi l'università è chiusa, studia a casa!")
    
    users[message.from_user.id] = prev_command


@bot.message_handler(func=lambda message: users[message.from_user.id] == "aula" and message.text in FreeRoom.buildings)
def print_classrooms_keyboard(message):
    global building
    
    building = message.text
    markup_classroom = make_classroom_keyboard_markup(building)

    bot.send_message(message.chat.id, "Scegli una classe:", reply_markup=markup_classroom)


@bot.message_handler(func=lambda message: users[message.from_user.id] == "edifici" and message.text in FreeRoom.buildings)
def print_free_hours_for_building(message):
    global building

    building = message.text
    free_times = FreeRoom.get_all_rooms_events_for_building(building)
    format_string = ""

    for room, free in free_times.items():
        if not free:
            format_string += room + " è occupata tutto il giorno\n"
        else:
            format_string += room + " è libera nei seguenti orari:\n"
            for interval in free:
                format_string += "- Dalle " + interval[0] + " alle " + interval[1] + "\n"
        format_string += "\n\n"

    bot.send_message(message.chat.id, format_string, reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda message: users[message.from_user.id] == "aula" and message.text in FreeRoom.rooms_for_buildings[FreeRoom.buildings[building]])
def print_free_hours_for_classroom(message):
    free_times = FreeRoom.get_all_rooms_events_for_building(building)[message.text]
    
    if not free_times:
        format_string = "L'aula è occupata tutto il giorno"
    else:
        format_string = "L'aula è libera nei seguenti orari:\n"

        for time in free_times:
            format_string += "- Dalle " + time[0] + " alle " + time[1] + "\n"

    bot.send_message(message.chat.id, format_string, reply_markup=telebot.types.ReplyKeyboardRemove())


bot.polling(none_stop=False)

while True:
    time.sleep(60*60)
    redis_connection.hmset("users", users)