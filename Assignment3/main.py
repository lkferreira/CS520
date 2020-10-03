import csv
import random
import copy
import sys


class Person:
    def __init__(self, event_time, bus_stop):
        self.event_time = event_time
        self.bus_stop = bus_stop
        self.event_type = 'person'


class Arrival:
    def __init__(self, event_time, bus_stop, bus_id):
        self.event_time = event_time
        self.bus_stop = bus_stop
        self.bus_id = bus_id
        self.event_type = 'arrival'


class Boarder:
    def __init__(self, event_time, bus_stop, bus_id):
        self.event_time = event_time
        self.bus_stop = bus_stop
        self.bus_id = bus_id
        self.event_type = 'boarder'


# sorted list class; creates a list and sorts it whenever new event is pushed
class SortedList:
    def __init__(self):
        self.list = []

    def push(self, event):
        self.list.append(event)
        self.list.sort(key=lambda x: x.event_time)

    def pop(self):
        return self.list.pop(0)

    def view_list(self):
        return self.list

# initialize simulation variables declared in
def initialize(event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_travel_time, bus_qty):
    for i in range(len(bus_queue)):
        event_list.push(Person(0, i))
        waiting_bus_queue.append([])

    for i in range(bus_qty):
        arrival_event = Arrival(bus_travel_time, round(i * (len(bus_queue) / bus_qty)), i)
        event_list.push(arrival_event)
        bus_current_locations.append({
            "last_stop": round(i * (len(bus_queue)/bus_qty)),
            "time_left": 0,
            "stop_count": 0
        })


# store simulation information so it can be later written into .csv file
def store_sim_info(bus_current_locations, bus_location_info, t, total_bus_stops, bus_queue, bus_travel_time):
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


# depart from bus stop
def bus_depart(t, event, event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_stop_flag, bus_travel_time):
    boarding_time = t + bus_travel_time

    # generate 'arrival' event at next bus stop
    event_list.push(Arrival(boarding_time, (event.bus_stop + 1) % len(bus_queue), event.bus_id))

    # alert approaching buses bus stop is free
    bus_stop_flag[event.bus_stop] = False

    # if there are any buses waiting to service bus stop, generate 'arrival' event for next bus
    if waiting_bus_queue[event.bus_stop]:
        bus_id = waiting_bus_queue[event.bus_stop].pop(0)
        event_list.push(Arrival(boarding_time, event.bus_stop, bus_id))

    # update current bus location info
    bus_current_locations[event.bus_id]['last_stop'] = event.bus_stop
    bus_current_locations[event.bus_id]['time_left'] = t
    bus_current_locations[event.bus_id]['stop_count'] += 1


# write simulation information into .csv file
def write_csv(bus_location_info, bus_queue, bus_qty):
    with open('bus_positions_test.csv', mode='w') as simulation_file:
        entry_writer = csv.writer(simulation_file, delimiter=',', lineterminator='\n', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        top_row = ['t(s)', 't[hr]']

        for i in range(bus_qty):
            top_row.append(f'Bus {i+1} - Pos')

        for i in range(bus_qty):
            top_row.append(f'Bus {i+1} - Dist')

        for i in range(len(bus_queue)):
            top_row.append(f'Queue {i+1} - Size')

        entry_writer.writerow(top_row)

        for entry in bus_location_info:
            positions = []
            positions.append(entry["t"])
            positions.append(entry["t"]/(60*60))

            for pos in entry["positions"]:
                positions.append(pos)

            for dist in entry["total_dist"]:
                positions.append(dist)

            for queue in entry["bus_queue"]:
                positions.append(queue)

            entry_writer.writerow(positions)


# bus simulation implementation
def bus_sim():
    t = 0                                                       # time variable (in seconds)
    simulation_time_hours = 8                                   # total simulation time (in hours)
    simulation_time = 60 * 60 * simulation_time_hours           # total simulation time (in seconds)
    total_bus_stops = 15                                        # number of bus stops
    bus_qty = 5                                                 # number of buses
    arrival_rate = 12                                           # mean arrival time in seconds for new passengers
    boarding_time = 2                                           # boarding time for each passenger
    bus_travel_time = 60*5                                      # time to drive b/w two bus stops
    bus_capacity = -1                                           # capacity of bus (for testing purposes; -1 for unlimited)

    event_list = SortedList()                                   # list of events
    bus_queue = [0] * total_bus_stops                           # list of bus queues
    bus_stop_flag = [False] * total_bus_stops                   # flag used to alert buses approaching a bus stop being serviced by another bus
    waiting_bus_queue = []                                      # queue used to keep track of buses waiting for a bus ahead to leave an occupied bus stop
    bus_current_locations = []                                  # list that keeps track of current location of each bus
    bus_location_info = []                                      # list used to save snapshots of simulation
    bus_passenger_count = [0] * bus_qty                         # count of passengers that have boarded a bus at a given bus stop (for testing purposes)

    # initialize variables and generate initial events
    initialize(event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_travel_time, bus_qty)

    # Redirect stdout to write out to file instead of console
    # sys.stdout = open('sample_output_IMPROVED', 'w')

    while t < simulation_time:

        # pop event from list of events
        event = event_list.pop()
        t = event.event_time

        if event.event_type == 'person':
            # generate exponentially distributed random new person 'arrival time'
            arrival_time = t + round(random.expovariate(1 / arrival_rate), 1)

            bus_queue[event.bus_stop] += 1
            event_list.push(Person(arrival_time, event.bus_stop))

        elif event.event_type == 'arrival':

            # if bus stop is NOT being serviced by another bus
            if not bus_stop_flag[event.bus_stop]:

                print(f'Bus {event.bus_id} arrived at bus stop {event.bus_stop} at time: {t} sec with queue of {bus_queue[event.bus_stop]} people')
                # alert any approaching buses that bus stop is occoupied
                bus_stop_flag[event.bus_stop] = True

                # if waiting queue is empty, leave bus stop and generate 'arrival' event at next stop
                if bus_queue[event.bus_stop] == 0:
                    bus_passenger_count[event.bus_id] = 0
                    bus_depart(t, event, event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_stop_flag, bus_travel_time)
                    print(f'Bus {event.bus_id} left bus stop {event.bus_stop} at time: {t} sec with queue of 0 people')
                # else generate a 'boarder' event
                else:
                    event_list.push(Boarder(t + boarding_time, event.bus_stop, event.bus_id))

            # if bus stop is being serviced by another bus, insert bus_id into queue
            else:
                waiting_bus_queue[event.bus_stop].append(event.bus_id)

        elif event.event_type == 'boarder':
            bus_queue[event.bus_stop] -= 1
            bus_passenger_count[event.bus_id] += 1

            # if waiting queue is empty OR bus has reached its capacity (for testing purposes), leave bus stop and generate 'arrival' event at next stop
            if bus_queue[event.bus_stop] == 0 or bus_passenger_count[event.bus_id] == bus_capacity:
                bus_passenger_count[event.bus_id] = 0
                bus_depart(t, event, event_list, bus_queue, waiting_bus_queue, bus_current_locations, bus_stop_flag, bus_travel_time)
                print(f'Bus {event.bus_id} left bus stop {event.bus_stop} at time: {t} sec with queue of 0 people')
            # else generate a 'boarder' event
            else:
                event_list.push(Boarder(t + boarding_time, event.bus_stop, event.bus_id))

        # store simulation information at given interval (currently set to every ~minute)
        if (t % 60*1) <= 2:
            store_sim_info(bus_current_locations, bus_location_info, t, total_bus_stops, bus_queue, bus_travel_time)

    print('---------------------------------------------------------------------------------')

    for i in range(len(bus_current_locations)):
        print(f'Bus {i} stops serviced count: {bus_current_locations[i]["stop_count"]}')

    # after simulation is done, write .csv file from bus_location_info list
    write_csv(bus_location_info, bus_queue, bus_qty)


# run simulation
bus_sim()