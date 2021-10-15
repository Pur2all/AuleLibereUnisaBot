import datetime
import json
from time import time
import requests
from collections import defaultdict

buildings = {
    "Aule Virtuali": "VIRT",
    "Campus Baronissi": "BCORPOA0-C0-D1-L1",
    "A1": "FRE-RATO",
    "A2": "FAUL-MAG",
    "B": "FSTEC-01",
    "B1": "FINV-01A",
    "B2": "FINV-02B",
    "C": "FSTEC-02-03",
    "C1": "FINV-03C",
    "C2": "FINV-04D",
    "D": "FSTEC-04",
    "D1": "FINV-05E",
    "D2": "FINV-06A",
    "D3": "FINV-08C",
    "E": "FSTEC-05-06",
    "E1": "FINV-09C",
    "E2": "FINV-07E",
    "F": "FSTEC-07-09",
    "F1": "FINV-11C",
    "F2": "FINV-12B",
    "F3": "FINV-13C",
    "I1": "FL-INGSA",
    "L2": "FL-ING03"
}

rooms_for_buildings = defaultdict(list)

events = None

url = "https://easycourse.unisa.it/AgendaStudenti//rooms_call.php"


def setup():
    global rooms_for_buildings

    response = requests.get(url)
    area_rooms = json.loads(response.content.decode("utf8"))["area_rooms"] # Getting dictionary key:building, value:rooms

    for building, rooms in area_rooms.items():
        for room_data in rooms.values():
            rooms_for_buildings[building].append(room_data["room_name"]) # Append name of rooms 


def get_only_time(list_of_times):
    len_of_list = len(list_of_times)

    for i in range(len_of_list):
        start, end = list_of_times[i][0], list_of_times[i][1]
        list_of_times[i] = (datetime.time(hour=start.hour, minute=start.minute),
                            datetime.time(hour=end.hour, minute=end.minute))

    return list_of_times


def format_time(list_of_times):
    len_of_list = len(list_of_times)

    for i in range(len_of_list):
        start, end = list_of_times[i][0], list_of_times[i][1]
        list_of_times[i] = (f"{start.hour:02d}:{start.minute:02d}",
                            f"{end.hour:02d}:{end.minute:02d}")

    return list_of_times


def extract_free_time(list_of_full_hours):
    assert list_of_full_hours is not None

    list_of_free_hours = []

    today = datetime.datetime.today()
    start_of_the_day = datetime.datetime(today.year, today.month, today.day, hour=8, minute=30)
    end_of_the_day = datetime.datetime(today.year, today.month, today.day, hour=19, minute=30)

    list_of_full_hours.insert(0, (None, start_of_the_day))
    list_of_full_hours.append((end_of_the_day, None))

    len_of_list = len(list_of_full_hours)
    i = 0

    while i < len_of_list - 1:
        next_occupied_from, this_occupied_to = list_of_full_hours[i + 1][0], list_of_full_hours[i][1]

        if next_occupied_from - this_occupied_to != datetime.timedelta(0):
            list_of_free_hours += [(this_occupied_to, next_occupied_from)]

        i += 1

    return get_only_time(list_of_free_hours)


def get_all_rooms_events_for_building(building=None):
    assert building is not None

    global events

    response = requests.get(url, params={"sede": buildings[building]})
    events = json.loads(response.content.decode("utf8"))["events"]

    room_events = {}
    for room in rooms_for_buildings[buildings[building]]:
        room_events[room] = []

    for event in events:
        occupied_from, occupied_to = datetime.datetime.fromtimestamp(event["timestamp_from"]), \
                                         datetime.datetime.fromtimestamp(event["timestamp_to"])
        room_events[event["NomeAula"]] += [(occupied_from, occupied_to)]
    
    for room, list_of_events_for_room in room_events.items():
        room_events[room] = extract_free_time(list_of_events_for_room)

    return room_events


def get_all_free_rooms_right_now(building=None):
    assert building is not None

    format_string = ""

    now = datetime.datetime.now()
    now = datetime.time(hour=now.hour, minute=now.minute)

    free_times = get_all_rooms_events_for_building(building)
    building_free_times_from_now = f"Nell'edificio {building} ci sono le seguenti aule libere in questo momento:\n"
    
    for room, free in free_times.items():
        if free:
            room_free_times_from_now = ""

            for start_free, end_free in free:
                if start_free < now < end_free:
                    room_free_times_from_now += f"fino alle {end_free.hour:02d}:{end_free.minute:02d}\n"
                    break
            
            if room_free_times_from_now != "":
                building_free_times_from_now += f"- {room} è libera {room_free_times_from_now}"

    if "libera" not in building_free_times_from_now:
        building_free_times_from_now = f"Nell'edificio {building} non ci sono aule libere in questo momento\n"
    
    format_string += building_free_times_from_now
    
    return format_string
