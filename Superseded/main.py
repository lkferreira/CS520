import csv
import random
import copy

class person:
    def __init__(self, event_time, bus_stop):
        self.event_time = event_time
        self.bus_stop = bus_stop

    event_type = 'person'


class arrival:
    def __init__(self, event_time, bus_stop, bus_id):
        self.event_time = event_time
        self.bus_stop = bus_stop
        self.bus_id = bus_id

    event_type = 'arrival'


class boarder:
    def __init__(self, event_time, bus_stop, bus_id):
        self.event_time = event_time
        self.bus_stop = bus_stop
        self.bus_id = bus_id

    event_type = 'boarder'


class sorted_list:
    def __init__(self):
        self.list = []

    def push(self, event):
        self.list.append(event)
        self.list.sort(key=lambda x: x.event_time)

    def pop(self):
        return self.list.pop(0)

    def view_list(self):
        return self.list


def initialize(event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_travel_time, bus_qty):
    for i in range(len(bus_queue)):
        event_list.push(person(0, i))
        waiting_bus_queue.append([])

    for i in range(bus_qty):
        arrival_event = arrival(bus_travel_time, round(i * (len(bus_queue)/bus_qty)), i)
        event_list.push(arrival_event)
        bus_current_locations.append({
            "last_stop": round(i * (len(bus_queue)/bus_qty)),
            "time_left": 0,
            "stop_count": 0
        })


def store_bus_position(bus_current_locations, bus_location_info, t, total_bus_stops, bus_queue, bus_travel_time):
    curr_locations_copy = copy.deepcopy(bus_current_locations)
    bus_queue_copy = copy.deepcopy(bus_queue)
    bus_positions = []
    bus_distances = []

    for bus in curr_locations_copy:
        dist_btw_stops = round((min((t - bus['time_left']), bus_travel_time) / bus_travel_time) * 10)
        bus_positions.append((bus['last_stop'] * 10 + dist_btw_stops) % (total_bus_stops * 10))
        bus_distances.append((bus['stop_count'] * 10 + dist_btw_stops))

    bus_location_info.append({
        "t": t,
        "bus_info": curr_locations_copy,
        "positions": bus_positions,
        "total_dist": bus_distances,
        "bus_queue": bus_queue_copy
    })


def bus_depart(t, event, event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_stop_flag, bus_travel_time, bus_wait_time):
    event_list.push(arrival(t + bus_travel_time, (event.bus_stop + 1) % len(bus_queue), event.bus_id))
    bus_stop_flag[event.bus_stop] = False

    if waiting_bus_queue[event.bus_stop]:
        bus_id = waiting_bus_queue[event.bus_stop].pop(0)
        event_list.push(arrival(t + bus_wait_time, event.bus_stop, bus_id))

    bus_current_locations[event.bus_id]['last_stop'] = event.bus_stop
    bus_current_locations[event.bus_id]['time_left'] = t
    bus_current_locations[event.bus_id]['stop_count'] += 1


def write_csv(bus_location_info):
    with open('bus_positions.csv', mode='w') as simulation_file:
        entry_writer = csv.writer(simulation_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        top_row = ['t(s)', 'Bus 1 - pos', 'Bus 2 - pos', 'Bus 3 - pos', 'Bus 4 - pos', 'Bus 5 - pos',
                                'Bus 1 - dist', 'Bus 2 - dist', 'Bus 3 - dist', 'Bus 4 - dist', 'Bus 5 - dist']

        for i in range(15):
            top_row.append(f'Queue {i+1} - Size')

        entry_writer.writerow(top_row)

        for entry in bus_location_info:
            positions = []
            positions.append(entry["t"])

            for pos in entry["positions"]:
                positions.append(pos)

            for dist in entry["total_dist"]:
                positions.append(dist)

            for queue in entry["bus_queue"]:
                positions.append(queue)

            entry_writer.writerow(positions)


def busSim():
    t = 0
    simulation_time_hours = 8
    simulation_time = 60 * 60 * simulation_time_hours
    total_bus_stops = 15
    bus_qty = 5
    arrival_rate = 12
    bus_travel_time = 60*5
    bus_wait_time = bus_travel_time
    bus_capacity = -1

    event_list = sorted_list()
    bus_queue = [0] * total_bus_stops
    stop_count = [0] * bus_qty
    bus_stop_flag = [False] * total_bus_stops
    waiting_bus_queue = []
    bus_current_locations = []
    bus_location_info = []
    bus_passenger_count = [0] * bus_qty

    initialize(event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_travel_time, bus_qty)

    while t < simulation_time:
        event = event_list.pop()
        t = event.event_time

        if event.event_type == 'person':
            arrival_time = t + round(random.expovariate(1 / arrival_rate), 1)
            bus_queue[event.bus_stop] += 1
            event_list.push(person(arrival_time, event.bus_stop))

        elif event.event_type == 'arrival':

            if not bus_stop_flag[event.bus_stop]:

                # print(f'bus {event.bus_id} arrived at bus stop {event.bus_stop} at {t} with {bus_queue[event.bus_stop]} boarders')
                stop_count[event.bus_id] += 1
                bus_stop_flag[event.bus_stop] = True

                if bus_queue[event.bus_stop] == 0:
                    bus_passenger_count[event.bus_id] = 0
                    bus_depart(t, event, event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_stop_flag, bus_travel_time, bus_wait_time)
                    # print(f'bus {event.bus_id} left bus stop {event.bus_stop} at {t} with NO boarders')
                else:
                    event_list.push(boarder(t + 2, event.bus_stop, event.bus_id))

            else:
                waiting_bus_queue[event.bus_stop].append(event.bus_id)

        elif event.event_type == 'boarder':
            bus_queue[event.bus_stop] -= 1
            bus_passenger_count[event.bus_id] += 1

            if bus_queue[event.bus_stop] == 0:
                bus_passenger_count[event.bus_id] = 0
                bus_depart(t, event, event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_stop_flag, bus_travel_time, bus_wait_time)
                # print(f'bus {event.bus_id} left bus stop {event.bus_stop} at {t} with boarders')
            elif bus_passenger_count[event.bus_id] == bus_capacity:
                bus_passenger_count[event.bus_id] = 0
                bus_depart(t, event, event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_stop_flag, bus_travel_time, bus_wait_time)
            else:
                event_list.push(boarder(t + 2, event.bus_stop, event.bus_id))

        if (t % 60*1) <= 2:
            store_bus_position(bus_current_locations, bus_location_info, t, total_bus_stops, bus_queue, bus_travel_time)

    for i in range(len(stop_count)):
        print(f'bus {i} count: {stop_count[i]}')

    write_csv(bus_location_info)


# list = sorted_list()
# list.push(person(1, 5))
# list.push(person(9, 5))
# list.push(person(2, 5))
# list.push(person(4, 5))
# list.push(person(3, 5))
#
# for item in list.view_list():
#     print(item.event_time)
# print('-----------------------')
#
# list.pop()
# list.pop()
#
# for item in list.view_list():
#     print(item.event_time)
# print('-----------------------')
#
# list = []
# for i in range(15):
#     val = neg_exp(1/30)
#     list.append(val)
#     # print(val)
#
# print(sum(list)/len(list))
# print('---------------------------')

busSim()