import search
import itertools
import json
import numpy as np
import collections

ids = ["207261983", "318403599"]


def state_per_one_taxi(state, specific_action) -> dict:
    if specific_action[0] == 'move':
        state['taxis'][specific_action[1]]['location'] = specific_action[2]
        state['taxis'][specific_action[1]]['fuel'] -= 1
        for passenger in state['passengers'].keys():
            if state['passenger_in_taxi'][passenger] == specific_action[1]:
                state['passengers'][passenger]['location'] = specific_action[2]
    elif specific_action[0] == 'pick up':
        state['unpicked'].remove(specific_action[2])
        state['passenger_in_taxi'][specific_action[2]] = specific_action[1]
        state['num_of_passengers_in_taxi'][specific_action[1]] += 1
    elif specific_action[0] == 'drop off':
        state['dropped_off'].append(specific_action[2])
        state['num_of_passengers_in_taxi'][specific_action[1]] -= 1
        state['passengers'][specific_action[2]]['location'] = state['passengers'][specific_action[2]]['destination']
    elif specific_action[0] == 'refuel':
        state['taxis'][specific_action[1]]['fuel'] = state['max_fuel'][specific_action[1]]
    return collections.OrderedDict(state)


def manhattan_distance(A, B):
    xA, yA = A
    xB, yB = B
    return abs(xA - xB) + abs(yA - yB)


def only_possible_permutations(permutations, state):
    """
    Returns only the possible permutations
    :param state:
    :param permutations:
    :return:
    """
    possible_permutations = []
    if len(state['taxis']) > 1:
        for permutation in permutations:
            all_locations = []
            all_actions = []
            for action in permutation:
                movement = action[0]
                taxi = action[1]
                if movement == 'move':
                    location = action[2]
                    all_locations.append(tuple(location))
                    all_actions.append(action)
                    all_actions.append('move')
                else:
                    all_actions.append(movement)
                    all_locations.append(tuple(state['taxis'][taxi]['location']))
            if len(all_locations) == len(set(all_locations)):
                possible_permutations.append(permutation)
    else:
        for permutation in permutations:
            permutation = permutation[len(permutation) - 1]
            possible_permutations.append(permutation)
    return possible_permutations


def to_tuples(state):
    """
    :param state:
    :return:
    """
    for taxi in state['taxis'].keys():
        state['taxis'][taxi]['Number_of_passengers'] = 0
        state['taxis'][taxi]['location'] = tuple(state['taxis'][taxi]['location'])
    for passenger in state['passengers'].keys():
        state['passengers'][passenger]['location'] = tuple(state['passengers'][passenger]['location'])
        state['passengers'][passenger]['destination'] = tuple(state['passengers'][passenger]['destination'])
    return state


def add_to_state(state):
    """
    Adds the taxi to the state
    :param state:
    :return:
    """
    state['passenger_in_taxi'] = {passenger: 'None' for passenger in state['passengers'].keys()}
    state = to_tuples(state)
    state['max_fuel'] = {taxi: state['taxis'][taxi]['fuel'] for taxi in state['taxis'].keys()}
    state['unpicked'] = [passenger for passenger in state['passengers'].keys()]
    state['num_of_passengers_in_taxi'] = {taxi: 0 for taxi in state['taxis'].keys()}
    state['dropped_off'] = []
    return collections.OrderedDict(state)


class TaxiProblem(search.Problem):
    """This class implements a medical problem according to problem description file"""

    def __init__(self, initial):
        """Don't forget to implement the goal test
        You should change the initial to your own representation.
        search.Problem.__init__(self, initial) creates the root node"""
        self.map = initial['map']
        search.Problem.__init__(self, json.dumps(add_to_state(initial), sort_keys=True))

    def possible_moves(self, state):
        """
        Returns all the possible moves
        :param state:
        :return:
        """
        moves = []
        rows = len(self.map) - 1
        cols = len(self.map[0]) - 1
        state = json.loads(state)
        state = to_tuples(state)
        for taxi in state['taxis'].keys():
            taxi_location = state['taxis'][taxi]['location']
            if state['taxis'][taxi]['fuel'] > 0:
                if taxi_location[0] - 1 >= 0:
                    if self.map[taxi_location[0] - 1][taxi_location[1]] != 'I':
                        moves.append(('move', taxi, (taxi_location[0] - 1, taxi_location[1])))
                if taxi_location[0] + 1 <= rows:
                    if self.map[taxi_location[0] + 1][taxi_location[1]] != 'I':
                        moves.append(('move', taxi, (taxi_location[0] + 1, taxi_location[1])))
                if taxi_location[1] - 1 >= 0:
                    if self.map[taxi_location[0]][taxi_location[1] - 1] != 'I':
                        moves.append(('move', taxi, (taxi_location[0], taxi_location[1] - 1)))
                if taxi_location[1] + 1 <= cols:
                    if self.map[taxi_location[0]][taxi_location[1] + 1] != 'I':
                        moves.append(('move', taxi, (taxi_location[0], taxi_location[1] + 1)))
        return moves

    def pickups(self, state):
        """
        Returns all the possible pickups
        """
        state = json.loads(state)
        state = to_tuples(state)
        pickups = []
        for passenger in state['passengers'].keys():
            for taxi in state['taxis'].keys():
                if state['passengers'][passenger]['location'] == state['taxis'][taxi]['location']:
                    if state['passenger_in_taxi'][passenger] == 'None' and \
                            state['num_of_passengers_in_taxi'][taxi] < state['taxis'][taxi]['capacity'] \
                            and passenger in state['unpicked']:
                        pickups.append(('pick up', taxi, passenger))
        json.dumps(state)
        return pickups

    def drop_offs(self, state):
        """
        Returns all the possible drop ups
        """
        state = json.loads(state)
        state = to_tuples(state)
        drop_ups = []
        for taxi in state['taxis'].keys():
            taxi_location = state['taxis'][taxi]['location']
            for passenger in state['passengers'].keys():
                if state['passenger_in_taxi'][passenger] == taxi:
                    if state['passengers'][passenger]['destination'] == taxi_location \
                            and passenger not in state['dropped_off'] \
                            and passenger not in state['unpicked']:
                        drop_ups.append(('drop off', taxi, passenger))
        json.dumps(state)
        return drop_ups

    def refuel(self, state):
        """
        Refuels the taxis
        """
        state = json.loads(state)
        state = to_tuples(state)
        refuels = []
        for taxi in state['taxis'].keys():
            taxi_location = state['taxis'][taxi]['location']
            if self.map[taxi_location[0]][taxi_location[1]] == 'G':
                refuels.append(('refuel', taxi))
        json.dumps(state)
        return refuels

    def waits(self, state):
        """
        Returns all the possible waits
        """
        state = json.loads(state)
        waits = []
        for taxi in state['taxis'].keys():
            waits.append(('wait', taxi))
        json.dumps(state)
        return waits

    def actions(self, state):

        """Returns all the actions that can be executed in the given
        state. The result should be a tuple (or other iterable) of actions
        as defined in the problem description file"""
        state = json.loads(state)
        actions = []
        moves = self.possible_moves(json.dumps(state))
        pickups = self.pickups(json.dumps(state))
        drop_ups = self.drop_offs(json.dumps(state))
        refuels = self.refuel(json.dumps(state))
        waits = self.waits(json.dumps(state))
        state = to_tuples(state)
        actions.extend(moves)
        actions.extend(pickups)
        actions.extend(drop_ups)
        actions.extend(refuels)
        actions.extend(waits)
        taxi_actions_dict = {taxi: [] for taxi in state['taxis'].keys()}
        for action in actions:
            taxi_actions_dict[action[1]].append(action)
        all_permutations = list(itertools.product(*taxi_actions_dict.values()))
        possible = only_possible_permutations(all_permutations, state)
        return possible

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        state = json.loads(state)
        state = to_tuples(state)
        if len(state['taxis'].keys()) == 1:
            state = state_per_one_taxi(state, action)
        else:
            for specific_action in list(action):
                state = state_per_one_taxi(state, specific_action)
        state = json.dumps(state)
        return state

    def goal_test(self, state):
        """ Given a state, checks if this is the goal state.
         Returns True if it is, False otherwise."""
        state = json.loads(state)
        state = to_tuples(state)
        if not state['unpicked'] and set(state['dropped_off']) == set(state['passengers'].keys()):
            return True
        return False

    def h(self, node):
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.State)
        and returns a goal distance estimate"""
        return self.h_2(node)

    def h_1(self, node):
        """
        This is a simple Manhattan heuristic
        """
        state = json.loads(node.state)
        number_of_waiting_passengers = 0
        for passenger in state['passenger_in_taxi'].keys():
            if state['passenger_in_taxi'][passenger] == 'None':
                number_of_waiting_passengers += 1
        number_of_taken_passengers = len(state['passengers']) - number_of_waiting_passengers
        number_of_taxi = len(state['taxis'])
        return (number_of_waiting_passengers * 2 + number_of_taken_passengers) / number_of_taxi

    def h_2(self, node):
        """
        This is a slightly more sophisticated Manhattan heuristic
        """
        state = json.loads(node.state)
        total_d = 0
        total_t = 0
        picked_up_but_not_dropped_off = state['unpicked'] + state['dropped_off']
        in_taxi = state['passengers'].keys() - picked_up_but_not_dropped_off
        for passenger in state['unpicked']:
            total_d += manhattan_distance(state['passengers'][passenger]['location'],
                                          state['passengers'][passenger]['destination'])
        for passenger in in_taxi:
            taxi = state['passenger_in_taxi'][passenger]
            total_t += manhattan_distance(state['passengers'][passenger]['destination'],
                                          state['taxis'][taxi]['location'])
        return total_d + total_t / len(state['taxis'].keys())


def create_taxi_problem(game):
    return TaxiProblem(game)
