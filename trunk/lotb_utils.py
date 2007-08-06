'''
Utilities for lord of the bots simulator
$Id$
'''
import os
import os.path
import sys

# directions
NORTH = 'north'
SOUTH = 'south'
EAST = 'east'
WEST = 'west'
NORTH_EAST = 'north_east'
NORTH_WEST = 'north_west'
SOUTH_EAST = 'south_east'
SOUTH_WEST = 'south_west'

DIRECTIONS = [NORTH, SOUTH, EAST, WEST, \
              NORTH_EAST, NORTH_WEST, \
              SOUTH_EAST, SOUTH_WEST]

MAX_HEALTH = 100
MAX_AMMO = 50

BUMP_HEALTH_LOSS = 5
FIRE_HEALTH_LOSS = 25

def import_module(module_path):
    '''
    imports a python module and
    returns the python object
    '''
    module_path = os.path.abspath(module_path)
    location = os.path.dirname(module_path)

    module_fname = os.path.basename(module_path)
    module_name = os.path.splitext(module_fname)[0]
    
    sys.path.insert(0, location)
    try:
        module = __import__(module_name)
    finally:
        del sys.path[0]

    return module

def bots_iter(teams):
    for t in teams:
        for b in t.bots:
            yield b

class Tile:
    def __init__(self):
        self.properties = {}

        # these affect the bot
        # that moves into this tile
        bot_props = {}

        # positive/negative can be used
        # eg: health = -5 or health = 5
        bot_props['health'] = 0
        bot_props['ammo'] = 0
        bot_props['deaths'] = 0
        bot_props['kills'] = 0
        bot_props['location'] = None
        
        # location property should be a tuple (row, col)
        # to teleport the bot to another location
        
        # whether tile is wall/floor
        is_obstruction = 0

        # init properties of tile
        self.properties = {}
        self.properties['bot'] = bot_props
        self.properties['is_obstruction'] = is_obstruction

    def get_properties(self):
        # used by simulator/bots to
        # gain information about tile
        return self.properties

    def use_properties(self):
        # called when the properties are used
        # by a bot. This can be used to update
        # properties.
        pass
    
    def update_properties(self):
        # this is called at the end-of-turn
        # can be used to update properties
        # in preparation for next turn
        pass

    def __int__(self):
        return self.properties['is_obstruction']

    def __nonzero__(self):
        is_obstruction = self.properties['is_obstruction']
        return bool(is_obstruction)

    def __eq__(self, obj):
        if isinstance(obj, int):
            is_obstruction = self.properties['is_obstruction']
            return is_obstruction == obj
        else:
            raise Exception('only int comparison allowed')

    def __repr__(self):
        return repr(int(self))

    def __str__(self):
        return repr(self)
            
class GameCustomizer:
    '''
    Used to customizer the game play.
    eg: deathmatch, last man standing etc
    '''
    def __init__(self):

        # max values for bot properties
        self.max = {}

        # maximum health a bot can possess
        self.max['health'] = MAX_HEALTH

        # maximum ammunition a bot can carry
        self.max['ammo'] = MAX_AMMO

        # health loss when a bot bumps into
        # obstruction/bot
        self.bump_health_loss = BUMP_HEALTH_LOSS

        # health loss when a bot gets fired at
        self.fire_health_loss = FIRE_HEALTH_LOSS

    def is_game_over(self, state):
        '''
        returns true when game is over
        '''
        return False # this is an infinite game!

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

    def get_leading_bot(self, state):
        '''
        return bot which is leading
        '''
        pass

    def get_leading_team(self, state):
        '''
        return the team which is leading
        '''
        pass

class DefaultGameCustomizer(GameCustomizer):
    def is_game_over(self, state):
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
            return True

        if state.game_time >= max_game_time:
            return True

        return False

    def get_leading_bot(self, state):
        '''
        return bot which is leading
        '''
        bots = [(b.kills, b) for b in bots_iter(state.teams)]
        bots.sort(reverse=True)

        return bots[0]

    def get_leading_team(self, state):
        '''
        return the team which is leading
        '''
        leading_bot = self.get_leading_bot(state)
        return leading_bot.team_name

