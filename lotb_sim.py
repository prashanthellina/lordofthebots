#!/usr/bin/env python

import optparse
import os, os.path
import glob
import random
import sys

import lotb_utils as utils

class Map:
    WALL_CELL = 1
    FLOOR_CELL = 0

    def __init__(self, name, data):
        self.rows = len(data)
        self.cols = len(data[0])
        self.map = data
        self.name = name
        self.active_tiles = {}

    def update_active_tiles(self):

        for rindex, row in enumerate(self.map):
            for cindex, col in enumerate(row):
                item = self.map[rindex, cindex]
                if isinstance(item, utils.Tile):
                    self.active_tiles[(rindex, cindex)] = item

    def get_tile_properties(self, location):
        row, col = location
        tile = self.map[row][col]
        if isinstance(tile, utils.Tile):
            properties = tite.get_properties()
            return properties

        return None

    def random_tile(self):
        row = random.randint(0, self.rows-1)
        col = random.randint(0, self.cols-1)
        return (row, col)

    def is_wall(self, location):
        row, col = location
        return self.map[row][col] == Map.WALL_CELL

    def is_floor(self, location):
        row, col = location
        return self.map[row][col] == Map.FLOOR_CELL

    def compute_location(self, location, direction):
        row, col = location

        if direction == utils.NORTH:
            row -= 1
        elif direction == utils.SOUTH:
            row += 1
        elif direction == utils.EAST:
            col -= 1
        elif direction == utils.WEST:
            col += 1
        elif direction == utils.NORTH_EAST:
            row -=1
            col -=1
        elif direction == utils.NORTH_WEST:
            row -= 1
            col += 1
        elif direction == utils.SOUTH_EAST:
            row += 1
            col -= 1
        elif direction == utils.SOUTH_WEST:
            row += 1
            col += 1
        return (row, col)

    def end_of_turn(self):
        '''
        called when a turn gets over
        '''
        for tile in self.active_tiles.itervalues():
            title.update_properties()

    def used_properties(self, location):
        if location in self.active_tiles:
            tile = self.active_tiles[location]
            title.use_properties()
            
class Team:
    def __init__(self, name, bots):
        self.name = name
        self.bots = []
        for bot_name, bot_obj in bots.iteritems():
            bot = Bot(bot_name, name, bot_obj)
            self.bots.append(bot)

class Bot:
    def __init__(self, name, team_name, bot_obj):
        self.name = name
        self.team_name = team_name
        self.obj = bot_obj

        self.max_health = 0
        self.health = 0

        self.max_ammo = 0
        self.ammo = 0

        self.location = None

        self.kills = 0  # number of other bots killed by self
        self.deaths = 0 # number of times killed

    def spawn(self, location, health, ammo):
        self.location = location
        
        self.max_health = health
        self.health = health

        self.max_ammo = ammo
        self.ammo = ammo

    def apply_property(self, property, value, max_value):
        cur_value = getattr(self, property, None)
        if cur_value is None: return

        cur_value += value
        if cur_value > max_value: cur_value = max_value

        setattr(self, property, cur_value)

    def perform(self, state):
        return self.obj.perform(state)

class Game:
    def __init__(self, map, teams, customizer, simlog):
        self.teams = teams
        self.map = map
        self.customizer = customizer
        self.simlog = simlog
        self.game_time = 0
        self.bot_locations = {}
        self.write_simlog_header()
        
        self.max_health = self.customizer.max['health']
        self.max_ammo = self.customizer.max['ammo']
        self.max_bot_actions = self.customizer.max_bot_actions

    def write_simlog_header(self):
        self.simlog.write('LOTB.DUMP.1\n')
        self.simlog.write('%s\n' % repr(self.map.map))
        self.simlog.write('%s\n' % repr([t.name for t in self.teams]))
        bots = [{'n':b.name, 't':b.team_name} for b in utils.bots_iter(self.teams)]
        self.simlog.write('%s\n' % bots)
        self.simlog.flush()

    def write_simlog(self, action, data):
        data = [self.game_time, action, data]
        self.simlog.write('%s\n' % data)

    def get_random_empty_tile(self):
        while 1:
            location = self.map.random_tile()
            if self.map.is_wall(location): continue
            if location in self.bot_locations: continue
            break

        return location

    def spawn_bot(self, bot):
        location = self.get_random_empty_tile()

        prev_location = bot.location
        if prev_location in self.bot_locations:
            del self.bot_locations[prev_location]

        bot.spawn(location, self.max_health, self.max_ammo)

        self.bot_locations[location] = bot

        data = {'bot':(bot.team_name, bot.name), 'loc': location}
        self.write_simlog('spawn', data)

    def spawn_bots(self):
        for team in self.teams:
            for bot in team.bots:
                self.spawn_bot(bot)

    def run(self):
        self.spawn_bots()
    
        game_over = False
        while not game_over:
            self.game_time += 1
            for team in self.teams:
                for bot in team.bots:
                    actions = bot.perform(self)
                    self.perform_actions(bot, actions)

            self.map.end_of_turn()
            
            game_over = self.customizer.is_game_over(self)

        self.write_simlog('game_over', None)

        return None

    def get_location_properties(self, action_location):
        is_wall = self.map.is_wall(action_location)
        is_floor = self.map.is_floor(action_location)
        bot_in_loc = self.bot_locations.get(action_location, None)
        properties = self.map.get_tile_properties(action_location)

        return (is_wall, is_floor, bot_in_loc, properties)

    def perform_move_action(self, bot, action_location, cur_loc):
        is_wall, is_floor, bot_in_loc, properties = self.get_location_properties(action_location)
        health_loss_reason = None

        if bot_in_loc: # reduce health points for both bots
            bot.health -= self.customizer.bump_health_loss
            bot_in_loc.health -= self.customizer.bump_health_loss
            health_loss_reason = 'bump'
            self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'health', 'v': bot.health })
            self.write_simlog('bot_param', {'b':(bot_in_loc.team_name, bot_in_loc.name), 't': 'health', 'v': bot.health})
        else:
            if is_wall:
                bot.health -= self.customizer.bump_health_loss
                health_loss_reason = 'bump'
                self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'health', 'v': bot.health })

            elif is_floor:
                bot.location = action_location
                del self.bot_locations[cur_loc]
                self.bot_locations[action_location] = bot
                self.write_simlog('move', {'b':(bot.team_name, bot.name), 'f': cur_loc, 't': action_location })

                if properties:
                    for bot_prop, value in properties.get('bot', {}):
                        if bot_prop == 'location': continue # location is handled differently
                        max_value = self.customizer.max.get(bot_prop, None)
                        if value != 0:
                            bot.apply_property(bot_prop, value, max_value)
                            final_value = bot.getattr(bot_prop, None)
                            self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': bot_prop, 'v': final_value })
                    self.map.used_properties(action_location)

                    if 'location' in properties:
                        new_loc = properties['location']
                        if new_loc and None not in new_loc:
                            bot_in_new_loc = self.bot_locations.get(new_loc, None)
                            if not bot_in_new_loc:
                                bot.location = new_loc
                                del self.bot_locations[action_location]
                                self.bot_locations[new_loc] = bot
                                self.write_simlog('move', {'b':(bot.team_name, bot.name), 'f': action_location, 't': new_loc })
            else:
                bot.health -= self.max_health
                health_loss_reason = 'fall'
                self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'health', 'v': bot.health })

        return health_loss_reason

    def perform_fire_action(self, bot, action_location, cur_loc):
        is_wall, is_floor, bot_in_loc, properties = self.get_location_properties(action_location)
        health_loss_reason = None
        
        self.write_simlog('fire', {'b':(bot.team_name, bot.name), 'f': cur_loc, 't': action_location })
        if bot_in_loc and bot.ammo:
            bot.ammo -= 1
            bot_in_loc.health -= self.customizer.fire_health_loss
            health_loss_reason = 'fire'
            self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'ammo', 'v': bot.ammo })
            self.write_simlog('bot_param', {'b':(bot_in_loc.team_name, bot_in_loc.name), 't': 'health', 'v': bot.health})
        elif bot.ammo:
            bot.ammo -= 1
            self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'ammo', 'v': bot.ammo })
        
        return health_loss_reason

    def perform_action(self, bot, action):
        action, direction = action.lower().split(' ')
        cur_loc = bot.location
        action_loc = self.map.compute_location(cur_loc, direction)
        is_wall = self.map.is_wall(action_loc)
        is_floor = self.map.is_floor(action_loc)
        bot_in_loc = self.bot_locations.get(action_loc, None)

        health_loss_reason = None

        if action == 'move':
            health_loss_reason = self.perform_move_action(bot, action_loc, cur_loc)

        elif action == 'fire':
            health_loss_reason = self.perform_fire_action(bot, action_loc, cur_loc)

        if bot.health <= 0:
            if health_loss_reason != 'fire':
                bot.kills -= 1 # 'kill' penalty for killing self
                self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'kills', 'v': bot.kills })
            bot.deaths += 1
            self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'deaths', 'v': bot.deaths })
            self.write_simlog('die', {'b':(bot.team_name, bot.name)})
            self.spawn_bot(bot)

        if bot_in_loc and bot_in_loc.health <= 0:
            bot_in_loc.deaths += 1
            bot.kills += 1
            self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'kills', 'v': bot.kills })
            self.write_simlog('bot_param', {'b':(bot_in_loc.team_name, bot_in_loc.name), 't': 'deaths', 'v': bot_in_loc.deaths})
            self.write_simlog('die', {'b':(bot_in_loc.team_name, bot_in_loc.name)})
            self.spawn_bot(bot_in_loc)

    def perform_actions(self, bot, actions):
        actions = actions[:self.max_bot_actions]
        for action in actions:
            self.perform_action(bot, action)
            
def load_teams(teams_dir):
    teams = []

    teams_dir = os.path.abspath(teams_dir)
    fpattern = os.path.join(teams_dir, '*/team.py')
    team_fnames = glob.glob(fpattern)

    for team_fname in team_fnames:
        #d = {}
        #team_code = file(team_fname).read()
        #exec(team_code) in d
        d = utils.import_module(team_fname)
        team_name = d.team_name
        bot_names = d.bots
        bots = dict([(bot_name, getattr(d, bot_name)) for bot_name in bot_names])

        team = Team(team_name, bots)

        teams.append(team)

    return teams

def load_map(map_file):
    map_file = os.path.abspath(map_file)

    #d = {}
    #map_code = file(map_file).read()
    #exec(map_code) in d
    d = utils.import_module(map_file)

    map_name = d.map_name
    map_data = d.map

    map = Map(map_name, map_data)
    return map

def load_game_customizer(game_file):
    game_file = os.path.abspath(game_file)

    #d = {}
    #game_code = file(game_file).read()
    #exec(game_code) in d
    d = utils.import_module(game_file)

    game_customizer = d.game
    return game_customizer

def main(options):
    teams = []
    if options.teams_dir:
        teams = load_teams(options.teams_dir)

    map = None
    if options.map_file:
        map = load_map(options.map_file)

    game_customizer = None
    if options.game_file:
        game_customizer = load_game_customizer(options.game_file)
    else:
        game_customizer = utils.DefaultGameCustomizer()

    simlog = sys.stdout
    if options.simulation_log:
        simlog = file(options.simulation_log, 'wb')

    game = Game(map, teams, game_customizer, simlog)

    stats = game.run()

if __name__ == "__main__":
    parser = optparse.OptionParser()
    
    parser.add_option('-t', '--teams-dir', metavar='DIR', help='directory of team dirs')
    parser.add_option('-m', '--map-file', metavar='FILE', help='map file')
    parser.add_option('-g', '--game-file', metavar='FILE', help='game file')
    parser.add_option('-s', '--simulation-log', metavar='FILE')

    options, args = parser.parse_args()
    main(options)
