#!/usr/bin/env python

import optparse
import os, os.path
import glob
import random
import sys

MAX_HEALTH = 100
MAX_AMMO = 50

HEALTH_BONUS = 25
AMMO_BONUS = 10

BUMP_HEALTH_LOSS = 5
FIRE_HEALTH_LOSS = 25

class Map:
    WALL_CELL = 1
    FLOOR_CELL = 0

    def __init__(self, name, data, bonus):
        self.rows = len(data)
        self.cols = len(data[0])
        self.map = data
        self.name = name
        self.bonus = dict([((r,c), bonus_type) for bonus_type, r, c in bonus])

    def random_cell(self):
        row = random.randint(0, self.rows-1)
        col = random.randint(0, self.cols-1)
        return (row, col)

    def is_wall(self, location):
        row, col = location
        return self.map[row][col] == Map.WALL_CELL

    def is_floor(self, location):
        row, col = location
        return self.map[row][col] == Map.FLOOR_CELL

    def get_bonus(self, location):
        row, col = location
        return self.bonus.get((row,col), None)

    def compute_location(self, location, direction):
        row, col = location
        if direction == 'north': row -= 1
        elif direction == 'south': row += 1
        elif direction == 'east': col -= 1
        elif direction == 'west': col += 1
        return (row, col)

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
        self.health = 0
        self.ammo = 0
        self.location = None

        self.kills = 0  # number of other bots killed by self
        self.deaths = 0 # number of times killed

    def spawn(self, location):
        self.location = location
        self.ammo = MAX_AMMO
        self.health = MAX_HEALTH

    def bonus(self, bonus):
        if bonus == 'health':
            self.health += HEALTH_BONUS
            if self.health > MAX_HEALTH:
                self.health = MAX_HEALTH
            return ('health', HEALTH_BONUS, self.health)

        elif bonus == 'ammo':
            self.ammo += AMMO_BONUS
            if self.ammo > MAX_AMMO:
                self.ammo = MAX_AMMO
            return ('ammo', AMMO_BONUS, self.ammo)

    def perform(self, state):
        return self.obj.perform(state)

def bots_iter(teams):
    for t in teams:
        for b in t.bots:
            yield b

class GameCustomizer:
    def check_game_over(self, state):
        winning_kills = 20
        max_game_time = 10000

        bots = [(b.kills, b) for b in bots_iter(state.teams)]
        bots.sort(reverse=True)

        kill, bot = bots[0]

        game_tied = False
        for k, b in bots[1:]:
            if k == kill:
                game_tied = True
                break

        if not game_tied and kill >= winning_kills:
            return [b for b in bots_iter(state.teams)]

        if state.game_time >= max_game_time:
            return [b for b in bots_iter(state.teams)]

        return None

    def collect_stats(self, state):
        pass

class Game:
    def __init__(self, map, teams, customizer, simlog):
        self.teams = teams
        self.map = map
        self.customizer = customizer
        self.simlog = simlog
        self.game_time = 0
        self.bot_locations = {}
        self.write_simlog_header()

    def write_simlog_header(self):
        self.simlog.write('LOTB.DUMP.1\n')
        self.simlog.write('%s\n' % repr(self.map.map))
        self.simlog.write('%s\n' % repr(self.map.bonus))
        self.simlog.write('%s\n' % repr([t.name for t in self.teams]))
        bots = [{'n':b.name, 't':b.team_name} for b in bots_iter(self.teams)]
        self.simlog.write('%s\n' % bots)
        self.simlog.flush()

    def write_simlog(self, action, data):
        data = [self.game_time, action, data]
        self.simlog.write('%s\n' % data)

    def get_random_empty_cell(self):
        while 1:
            location = self.map.random_cell()
            if self.map.is_wall(location): continue
            if location in self.bot_locations: continue
            break

        return location

    def spawn_bot(self, bot):
        location = self.get_random_empty_cell()

        prev_location = bot.location
        if prev_location in self.bot_locations:
            del self.bot_locations[prev_location]

        bot.spawn(location)

        self.bot_locations[location] = bot

        data = {'bot':(bot.team_name, bot.name), 'loc': location}
        self.write_simlog('spawn', data)

    def spawn_bots(self):
        for team in self.teams:
            for bot in team.bots:
                self.spawn_bot(bot)

    def run(self):
        self.spawn_bots()
    
        game_over_stats = None
        while not game_over_stats:
            self.game_time += 1
            for team in self.teams:
                for bot in team.bots:
                    actions = bot.perform(self)
                    self.perform_actions(bot, actions)
            
            game_over_stats = self.customizer.check_game_over(self)

        bots = game_over_stats

        data = [{'b':(b.team_name, b.name), 'h':b.health, 'a': b.ammo, 'k': b.kills, 'd': b.deaths}
                for b in bots
               ]

        self.write_simlog('game_over', data)

        return game_over_stats

    def perform_action(self, bot, action):
        action, direction = action.lower().split(' ')
        cur_loc = bot.location
        action_loc = self.map.compute_location(cur_loc, direction)
        is_wall = self.map.is_wall(action_loc)
        is_floor = self.map.is_floor(action_loc)
        bot_in_loc = self.bot_locations.get(action_loc, None)

        health_loss_reason = None
        
        if action == 'move':
            if bot_in_loc: # reduce health points for both bots
                bot.health -= BUMP_HEALTH_LOSS
                bot_in_loc.health -= BUMP_HEALTH_LOSS
                health_loss_reason = 'bump'
                self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'health', 'v': bot.health })
                self.write_simlog('bot_param', {'b':(bot_in_loc.team_name, bot_in_loc.name), 't': 'health', 'v': bot.health})
            else:
                if is_wall:
                    bot.health -= BUMP_HEALTH_LOSS
                    health_loss_reason = 'bump'
                    self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'health', 'v': bot.health })

                elif is_floor:
                    bot.location = action_loc
                    del self.bot_locations[cur_loc]
                    self.bot_locations[action_loc] = bot
                    bonus = self.map.get_bonus(action_loc)
                    self.write_simlog('move', {'b':(bot.team_name, bot.name), 'f': cur_loc, 't': action_loc })
                    if bonus:
                        bonus_type, change_value, final_value = bot.bonus(bonus)
                        self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': bonus_type, 'v': final_value })
                else:
                    bot.health -= MAX_HEALTH
                    health_loss_reason = 'fall'
                    self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'health', 'v': bot.health })

        if action == 'fire':
            self.write_simlog('fire', {'b':(bot.team_name, bot.name), 'f': cur_loc, 't': action_loc })
            if bot_in_loc and bot.ammo:
                bot.ammo -= 1
                bot_in_loc.health -= FIRE_HEALTH_LOSS
                health_loss_reason = 'fire'
                self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'ammo', 'v': bot.ammo })
                self.write_simlog('bot_param', {'b':(bot_in_loc.team_name, bot_in_loc.name), 't': 'health', 'v': bot.health})
            elif bot.ammo:
                bot.ammo -= 1
                self.write_simlog('bot_param', {'b':(bot.team_name, bot.name), 't': 'ammo', 'v': bot.ammo })

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
        actions = actions[:2] # permit max of 2 actions per turn
        for action in actions:
            self.perform_action(bot, action)
            

def load_teams(teams_dir):
    teams = []

    teams_dir = os.path.abspath(teams_dir)
    fpattern = os.path.join(teams_dir, '*/team.py')
    team_fnames = glob.glob(fpattern)

    for team_fname in team_fnames:
        d = {}
        team_code = file(team_fname).read()
        exec(team_code) in d
        team_name = d['team_name']
        bot_names = d['bots']
        bots = dict([(bot_name, d[bot_name]) for bot_name in bot_names])

        team = Team(team_name, bots)

        teams.append(team)

    return teams

def load_map(map_file):
    map_file = os.path.abspath(map_file)

    d = {}
    map_code = file(map_file).read()
    exec(map_code) in d

    map_name = d['map_name']
    map_data = d['map']
    bonus = d['bonus']

    map = Map(map_name, map_data, bonus)
    return map

def load_game_customizer(game_file):
    game_file = os.path.abspath(game_file)

    d = {}
    game_code = file(game_file).read()
    exec(game_code) in d

    game_customizer = d['game']
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
        game_customizer = GameCustomizer()

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
