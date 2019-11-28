import telebot
from FreeRoom import *

TOKEN = "783944951:AAHdmcNjyI-8fZsSKv_-hIMp5MLeBkbDUvc"


def make_buildings_keyboard_markup():
    markup = telebot.types.ReplyKeyboardMarkup()
    buttons = []

    for key in buildings:
        temp_button = telebot.types.KeyboardButton(text=key)
        buttons.append(temp_button)
    markup.add(*buttons)

    return markup


def make_classroom_keyboard_markup(building):
    markup = telebot.types.ReplyKeyboardMarkup()
    buttons = []
    values = rooms_for_buildings[building]

    for value in values:
        temp_button = telebot.types.KeyboardButton(value)
        buttons.append(temp_button)
    markup.add(*buttons)

    return markup


setup()
bot = telebot.TeleBot(TOKEN)
building: str = None


@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Questo è un bot per cercare le aule libere ad Unisa, buona fortuna!")


@bot.message_handler(commands=["edifici"])
def print_buildings_keyboard(message):
    markup = make_buildings_keyboard_markup()

    bot.send_message(message.chat.id, "Scegli un edificio:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in buildings)
def print_rooms_keyboard(message):
    global building

    building = message.text
    markup = make_classroom_keyboard_markup(buildings[building])

    bot.send_message(message.chat.id, "Scegli un'aula:", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text in rooms_for_buildings[buildings[building]])
def print_free_hours(message):
    free_times = extract_free_time(get_all_rooms_events(building)[message.text])

    format_string = "L'aula è libera nei seguenti orari:\n"

    for time in free_times:
        format_string += "- Dalle " + time[0] + " alle " + time[1] + "\n"

    bot.send_message(message.chat.id, format_string, reply_markup=telebot.types.ReplyKeyboardRemove())


bot.polling(none_stop=False)
