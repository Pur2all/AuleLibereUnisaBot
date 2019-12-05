import datetime
import requests
import json
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
    area_rooms = json.loads(response.content.decode("utf8"))["area_rooms"]

    for key, value in area_rooms.items():
        for room_id, data in value.items():
            rooms_for_buildings[key].append(data["room_name"])


def format_time(list_of_times):
    len_of_list = len(list_of_times)

    for i in range(len_of_list):
        start, end = list_of_times[i][0], list_of_times[i][1]
        list_of_times[i] = ("{:02d}:{:02d}".format(start.hour, start.minute),
                            "{:02d}:{:02d}".format(end.hour, end.minute))

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

    return format_time(list_of_free_hours)


# Se vuoi farlo per un aula singola il parametro da mettere è quello dell'ID del JSON, ad esempio P11 è FINV-13CP01003
def get_all_rooms_events_for_building(of_building=None):
    assert of_building is not None

    global events

    response = requests.get(url, params={"sede": buildings[of_building]})
    events = json.loads(response.content.decode("utf8"))["events"]

    room_events = {}
    for room in rooms_for_buildings[buildings[of_building]]:
        room_events[room] = []

    for event in events:
        occupied_from, occupied_to = datetime.datetime.fromtimestamp(event["timestamp_from"]), \
                                         datetime.datetime.fromtimestamp(event["timestamp_to"])
        room_events[event["NomeAula"]] += [(occupied_from, occupied_to)]
    
    for room, list_of_events_for_room in room_events.items():
        room_events[room] = extract_free_time(list_of_events_for_room)

    return room_events
