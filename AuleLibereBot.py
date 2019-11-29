import telebot
import FreeRoom

TOKEN = "783944951:AAHdmcNjyI-8fZsSKv_-hIMp5MLeBkbDUvc"


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
prev_command : str = None

@bot.message_handler(commands=["start"])
def send_welcome(message):
    bot.send_message(message.chat.id, "Questo è un bot per cercare le aule libere ad Unisa, buona fortuna!")


@bot.message_handler(commands=["edifici", "aula"])
def print_buildings_keyboard(message):
    global prev_command

    prev_command = message.text.replace("/", "")
    markup = make_buildings_keyboard_markup()

    bot.send_message(message.chat.id, "Scegli un edificio:", reply_markup=markup)


@bot.message_handler(func=lambda message: prev_command == "aula" and message.text in FreeRoom.buildings)
def print_classrooms_keyboard(message):
    global building

    building = message.text
    markup_classroom = make_classroom_keyboard_markup(building)

    bot.send_message(message.chat.id, "Scegli una classe:", reply_markup=markup_classroom)


@bot.message_handler(func=lambda message: prev_command == "edifici" and message.text in FreeRoom.buildings)
def print_free_hours_for_building(message):
    global building
    
    building = message.text
    free_times = FreeRoom.get_all_rooms_events_for_building(building)
    format_string = ""

    for room, free in free_times.items():
        format_string += room + " è libera nei seguenti orari:\n"
        for interval in free:
            format_string += "- Dalle " + interval[0] + " alle " + interval[1] + "\n"
        format_string += "\n\n"

    bot.send_message(message.chat.id, format_string, reply_markup=telebot.types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda message: prev_command == "aula" and message.text in FreeRoom.rooms_for_buildings[FreeRoom.buildings[building]])
def print_free_hours_for_classroom(message):
    free_times = FreeRoom.get_all_rooms_events_for_building(building)[message.text]

    format_string = "L'aula è libera nei seguenti orari:\n"

    for time in free_times:
        format_string += "- Dalle " + time[0] + " alle " + time[1] + "\n"

    bot.send_message(message.chat.id, format_string, reply_markup=telebot.types.ReplyKeyboardRemove())


bot.polling(none_stop=False)
